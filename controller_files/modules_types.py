# -*- coding: utf-8 -*-
from json import loads as jloads
from urllib.parse import unquote

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

from ..modules.auth_utils import basic_auth

# Define the base route for the module_types controller
base_route = "api/module_types/"

# try something like
def index(): return dict(message="hello from modules_types.py")

# Function to check if the payload contains all the required fields.
def get_valid_payload(required_fields):
    payload = request.body.read()
    if not payload:
        return None, "No payload given."
    payload = jloads(payload)
    for field in required_fields:
        if field not in payload:
            return None, f"Payload missing required field: {field}."
    return payload, None

# Create a new module type from a given payload. Throws an error if no payload is given, or the module type already exists.
@action(base_route + "create", method="POST")
@action.uses(db)
@basic_auth(auth)
def create_module_type():
    payload, error = get_valid_payload(['name', 'description'])
    if error:
        return dict(msg=error)
    if db(db.module_types.name == payload['name']).count() > 0:
        return dict(msg="Module Type already exists.")
    
    db.module_types.insert(name=payload['name'], description=payload['description'])
    return dict(msg="Module Type created.")

# Get a module type by name. Throws an error if no name is given, or the module type does not exist.
@action(base_route + "get/<name>", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_module_type(name):
    name = waddle_helpers.decode_name(name)
    if name is None:
        return dict(msg="No name given.")
    module_type = db(db.module_types.name == name).select().first()
    if module_type is None:
        return dict(msg="Module Type does not exist.")
    return dict(module_type=module_type)

# Get all module types.
@action(base_route + "get_all", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_all_module_types():
    module_types = db(db.module_types).select()
    return dict(data=module_types)

# Update a module type by name. Throws an error if no name is given, or the module type does not exist.
@action(base_route + "update/<name>", method="PUT")
@action.uses(db)
@basic_auth(auth)
def update_module_type(name):
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    module_type = db(db.module_types.name == name).select().first()
    if not module_type:
        return dict(msg="Module Type does not exist.")
    payload, error = get_valid_payload(['name', 'description'])
    if error:
        return dict(msg=error)
    db(db.module_types.name == name).update(**payload)
    return dict(msg="Module Type updated.")

# Delete a module type by name. Throws an error if no name is given, or the module type does not exist.
@action(base_route + "delete/<name>", method="DELETE")
@action.uses(db)
@basic_auth(auth)
def delete_module_type(name):
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    module_type = db(db.module_types.name == name).select().first()
    if not module_type:
        return dict(msg="Module Type does not exist.")
    db(db.module_types.name == name).delete()
    return dict(msg="Module Type deleted.")