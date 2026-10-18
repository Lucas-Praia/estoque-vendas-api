"""Guarda a requisição atual para que logs e auditoria saibam quem fez o quê, sem passar isso por parâmetro."""

from contextvars import ContextVar

_current_request = ContextVar('current_request', default=None)
_current_request_id = ContextVar('current_request_id', default='-')


def set_request(request, request_id):
    return _current_request.set(request), _current_request_id.set(request_id)


def reset_request(tokens):
    request_token, request_id_token = tokens
    _current_request.reset(request_token)
    _current_request_id.reset(request_id_token)


def get_request_id():
    return _current_request_id.get()


def get_user():
    """Usuário autenticado da requisição atual (o DRF preenche request.user ao validar o JWT)."""
    request = _current_request.get()
    user = getattr(request, 'user', None)
    return user if user is not None and user.is_authenticated else None


def get_client_info():
    request = _current_request.get()
    if request is None:
        return {'tx_ip': None, 'tx_user_agent': ''}
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
    return {'tx_ip': ip or None, 'tx_user_agent': request.META.get('HTTP_USER_AGENT', '')[:255]}
