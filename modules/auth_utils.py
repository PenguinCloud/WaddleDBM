import base64
import logging
from py4web import HTTP, request

"""
Basic example of how to use the basic_auth decorator:

from py4web import action, HTTP
from .auth_utils import basic_auth

@action("protected")
@basic_auth(auth)
def protected():
    return "This is a protected endpoint"
"""

def basic_auth(auth):
    """
    A decorator to enforce Basic Authentication for endpoints.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Basic '):
                raise HTTP(401, "Unauthorized", headers={'WWW-Authenticate': 'Basic realm="Login Required"'})

            # Decode the Base64-encoded credentials
            try:
                auth_decoded = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
                username, password = auth_decoded.split(':', 1)
            except Exception:
                raise HTTP(400, "Invalid Authorization Header")

            logging.info(f"Authenticating user {username}")

            # Manually validate the credentials against the auth_user table
            user = auth.db(auth.db.auth_user.username == username).select().first()
            if not user or not auth.db.auth_user.password.validate(password)[0] == user.password:
                raise HTTP(401, "Invalid credentials", headers={'WWW-Authenticate': 'Basic realm="Login Required"'})

            # If authenticated, proceed to the endpoint
            return func(*args, **kwargs)
        return wrapper
    return decorator

