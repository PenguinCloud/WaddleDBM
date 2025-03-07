# -*- coding: utf-8 -*-
from json import loads as jloads

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

# Define the base route for the identities controller
base_route = "api/identities/"

# try something like
def index(): return dict(message="hello from identities.py")

# Create a new identity from a given payload. Throws an error if no payload is given, or the identity already exists.
def create():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'name' not in payload or 'country' not in payload or 'ip_address' not in payload or 'browser_fingerprints' not in payload:
        return dict(msg="Payload missing required fields.")
    if db(db.identities.name == payload['name']).count() > 0:
        return dict(msg="Identity already exists.")
    db.identities.insert(name=payload['name'], country=payload['country'], ip_address=payload['ip_address'], browser_fingerprints=payload['browser_fingerprints'])
    return dict(msg="Identity created.")

# Get all identities.
def get_all():
    identities = db(db.identities).select()
    return dict(data=identities)

# Get an identity by its name. If the identity does not exist, return an error.
def get_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    identity = db(db.identities.name == name).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    return dict(data=identity)

# Update an identity by its name. If the identity does not exist, return an error.
def update_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'name' not in payload or 'country' not in payload or 'ip_address' not in payload or 'browser_fingerprints' not in payload:
        return dict(msg="Payload missing required fields.")
    identity = db(db.identities.name == name).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    identity.update_record(name=payload['name'], country=payload['country'], ip_address=payload['ip_address'], browser_fingerprints=payload['browser_fingerprints'])
    return dict(msg="Identity updated.")

# Delete an identity by its name. If the identity does not exist, return an error.
def delete_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    identity = db(db.identities.name == name).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    identity.delete_record()
    return dict(msg="Identity deleted.")