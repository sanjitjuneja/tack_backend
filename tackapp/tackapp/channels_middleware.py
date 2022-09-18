import logging

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

from user.models import User


logger = logging.getLogger()


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


def extract_token(headers: tuple) -> bytes:
    """Function to get token from HTTP headers"""

    # Starting from an end because "Authorization" header will likely be there
    for header, value in headers[::-1]:
        if header == b'authorization':
            return value
    return b''


def extract_device_info(headers: tuple) -> bytes:
    """Function to get device_id from HTTP headers"""

    # Starting from an end because "Authorization" header will likely be there
    for header, value in headers[::-1]:
        if header == b'device-info':
            return value
    return b'No device info'


class TokenAuthMiddleware:
    """
    Custom token auth middleware
    """

    def __init__(self, inner):
        # Store the ASGI application we were passed
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()

        # Get the token
        token = extract_token(scope['headers'])
        device_info = extract_device_info(scope['headers'])
        logger.warning(f"{scope['headers'] = }")
        logger.warning(f"{token = }")

        # Try to authenticate the user
        try:
            # This will automatically validate the token and raise an error if token is invalid
            UntypedToken(token)
            # TODO: if token is not Blacklisted
        except (InvalidToken, TokenError) as e:
            # Token is invalid
            logger.warning(f"{e = }")
            return None
        else:
            #  Then token is valid, decode it
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            logger.warning(f"{decoded_data = }")
            # Will return a dictionary like -
            # {
            #     "token_type": "access",
            #     "exp": 1568770772,
            #     "jti": "5c15e80d65b04c20ad34d77b6703251b",
            #     "user_id": 6
            # }

            # Get the user using ID
            user = await get_user(int(decoded_data["user_id"]))
            logger.warning(f"{user = }")
        # Return the inner application directly and let it run everything else
        return await self.inner(dict(scope, user=user, device_info=device_info), receive, send)
