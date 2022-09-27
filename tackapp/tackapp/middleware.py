import logging
import time
from threading import local

thread_locals = local()
time_measurement_logger = logging.getLogger("sql_time_measurement")


class RequestTimeMiddleware:
    """Middleware for logging server time request response"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        thread_locals.path = request.path
        timestamp = time.monotonic()

        response = self.get_response(request)

        time_measurement_logger.debug((
            f'{request.path} :: {time.monotonic() - timestamp:.3f} sec'))
        thread_locals.path = ''

        return response
