import logging
import re
import time
import uuid

from . import context

logger = logging.getLogger('audit.request')

REQUEST_ID_HEADER = 'X-Request-ID'
VALID_REQUEST_ID = re.compile(r'^[A-Za-z0-9-]{1,64}$')


class RequestContextMiddleware:
    """Dá um ID a cada requisição, devolve no cabeçalho X-Request-ID e registra método, rota, status e duração."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = self._request_id_from(request)
        tokens = context.set_request(request, request_id)
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            self._log(request, response, started)
            return response
        finally:
            context.reset_request(tokens)

    @staticmethod
    def _request_id_from(request):
        """Reaproveita o ID enviado pelo front (para ligar os dois lados) se for seguro; senão gera um novo."""
        incoming = request.headers.get(REQUEST_ID_HEADER, '')
        return incoming if VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex

    @staticmethod
    def _log(request, response, started):
        user = context.get_user()
        logger.info(
            '%s %s %s',
            request.method,
            request.path,
            response.status_code,
            extra={
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round((time.perf_counter() - started) * 1000, 1),
                'user': user.get_username() if user else None,
                'ip': context.get_client_info()['tx_ip'],
            },
        )
