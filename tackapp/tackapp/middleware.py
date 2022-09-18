import logging
import os
import sys
import time
from threading import local

from tackapp.log import build_logger

thread_locals = local()

time_measurement_logger = build_logger("tackapp.middleware")
FORMAT = "\n%(asctime)23s :: %(name)-15s :: line %(lineno)5s :: %(message)20s"
# time_measurement_logger = logging.getLogger("tackapp.middleware")
time_measurement_logger.setLevel("CRITICAL")

log_filename = "logs/time_measurement.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)

# sh = logging.StreamHandler(sys.stdout)
# sh.setLevel("CRITICAL")

fh = logging.FileHandler(filename=log_filename)
fh.setFormatter(logging.Formatter(FORMAT))
time_measurement_logger.addHandler(fh)
# time_measurement_logger.addHandler(sh)

logging.basicConfig(filename=log_filename)

logging.getLogger().warning(time_measurement_logger.handlers)


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
