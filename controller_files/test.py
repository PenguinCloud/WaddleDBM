# -*- coding: utf-8 -*-
from py4web import URL, abort, action, redirect, request

from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)
                     
base_route = "api/things/"

@action(base_route + "get_all", method="GET")
@action.uses(db)
def api_GET_things():
    return {"things": db(db.thing).select().as_list()}
    
@action(base_route + "post_value", method="POST")
@action.uses(db)
def api_POST_things():
    return db.thing.validate_and_insert(**request.json)