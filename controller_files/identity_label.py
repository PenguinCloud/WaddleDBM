# -*- coding: utf-8 -*-
from json import loads as jloads

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

from ..modules.auth_utils import basic_auth

# Define the base route for the identity_label controller
base_route = "api/identity_label/"

# try something like
def index(): return dict(message="hello from identity_label.py")

# A helper function to parse the payload of a request.
def parse_payload() -> dict:
    payload = request.body.read()
    if not payload:    
        raise ValueError("No payload given.")
    return payload

# Function to create a new identity label for a given identity_name and community_name.
# Throws an error if no identity_name or community_name is given, or the identity label already exists.
# Also throws an error if the identity or the community does not exist.
@action(base_route + "create", method="POST")
@action.uses(db)
@basic_auth(auth)
def create():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the identity_label to the first element in the command string list.
    identity_label_val = command_str_list[0]
    
    # Check if the identity label already exists.
    if db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).count() > 0:
        return dict(msg="Identity label already exists.")
    
    # Insert the identity label.
    db.identity_labels.insert(identity_id=identity.id, community_id=community.id, label=identity_label_val)

    return dict(msg="Identity label created.")

# Get all identity labels for a given identity name and community name in a payload object.
@action(base_route + "get_by_identity_and_community", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_by_identity_and_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    identity = payload['identity']

    # Get all identity labels for the given identity name and community name.
    identity_labels = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select()
    
    return dict(data=identity_labels)

# Function to update an identity label for a given identity name and community name.
# Throws an error if no identity name, community name or label is given, or the identity label does not exist.
@action(base_route + "update_by_identity_and_community", method="PUT")
@action.uses(db)
@basic_auth(auth)
def update_by_identity_and_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the identity_label to the first element in the command string list.
    identity_label_val = command_str_list[0]
    
    # Check if the identity label exists.
    identity_label = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select().first()
    if not identity_label:
        return dict(msg="Identity label does not exist.")
    
    # Update the identity label.
    identity_label.update_record(label=identity_label_val)
    
    return dict(msg="Identity label updated.")

# Function to delete an identity label for a given identity name and community name.
# Throws an error if no identity name or community name is given, or the identity label does not exist.
@action(base_route + "delete_by_identity_and_community", method="DELETE")
@action.uses(db)
@basic_auth(auth)
def delete_by_identity_and_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    identity = payload['identity']
    
    # Check if the identity label exists.
    identity_label = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select().first()
    if not identity_label:
        return dict(msg="Identity label does not exist.")
    
    # Delete the identity label.
    identity_label.delete_record()
    
    return dict(msg="Identity label deleted.")
