# -*- coding: utf-8 -*-
from json import loads as jloads
from urllib.parse import unquote


# try something like
def index(): return dict(message="hello from marketplace.py")

# Create a new module type from a given payload. Throws an error if no payload is given, or the module type already exists.
def create_module_type():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'name' not in payload or 'description' not in payload:
        return dict(msg="Payload missing required fields.")
    if db(db.module_types.name == payload['name']).count() > 0:
        return dict(msg="Module Type already exists.")
    
    db.module_types.insert(name=payload['name'], description=payload['description'])
    return dict(msg="Module Type created.")

# Get a module type by name. Throws an error if no name is given, or the module type does not exist.
def get_module_type():
    if name := waddle_helpers.decode_name(request.args(0)) is None:
        return dict(msg="No name given.")
    elif module_type := db(db.module_types.name == name).select().first() is None:
        return dict(msg="Module Type does not exist.")
    else:
        return dict(module_type=module_type)

# Get all module types.
def get_all_module_types():
    module_types = db(db.module_types).select()
    return dict(data=module_types)

# Update a module type by name. Throws an error if no name is given, or the module type does not exist.
def update_module_type():
    name = waddle_helpers.decode_name(request.args(0))
    if not name:
        return dict(msg="No name given.")
    module_type = db(db.module_types.name == name).select().first()
    if not module_type:
        return dict(msg="Module Type does not exist.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    db(db.module_types.name == name).update(**payload)
    return dict(msg="Module Type updated.")

# Delete a module type by name. Throws an error if no name is given, or the module type does not exist.
def delete_module_type():
    name = waddle_helpers.decode_name(request.args(0))
    if not name:
        return dict(msg="No name given.")
    module_type = db(db.module_types.name == name).select().first()
    if not module_type:
        return dict(msg="Module Type does not exist.")
    db(db.module_types.name == name).delete()
    return dict(msg="Module Type deleted.")
