# -*- coding: utf-8 -*-
from py4web import URL, abort, action, redirect, request

from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers
from ..modules.auth_utils import basic_auth

# Define the base route for the test_script controller
base_route = "api/test_script/"

# A test function call
@action(base_route + "test", method="GET")
@action.uses(db)
@basic_auth(auth)
def test():
    return dict(msg="HELLO FROM MY TEST SCRIPT!")