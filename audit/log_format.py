"""Logs em JSON (uma linha por evento), prontos para buscar por request_id nos logs do container."""

import json
import logging
from datetime import datetime, timezone

from . import context

_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {'message', 'asctime', 'request_id'}


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = context.get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'request_id': getattr(record, 'request_id', '-'),
            'message': record.getMessage(),
        }
        entry.update({key: value for key, value in vars(record).items() if key not in _STANDARD_ATTRS})
        if record.exc_info:
            entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)
