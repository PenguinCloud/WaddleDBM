# -*- coding: utf-8 -*-
from json import loads as jloads

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

from ..modules.auth_utils import basic_auth

# Define the base route for the community_modules controller
base_route = "api/community_modules/"

# try something like
def index(): return dict(message="hello from communities_modules.py")

# Get all community modules accross all communities.
def get_all():
    community_modules = db(db.community_modules).select()
    return dict(data=community_modules, status=200)

# Get all community modules for a given community name.
def get_by_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    community_modules = db(db.community_modules.community_id == community.id).select()
    return dict(data=community_modules, status=200)

def get_lookup(community_name, identity_name, module_name):
    query = (
        (db.communities.community_name == community_name) &
        (db.identities.name == identity_name) &
        (db.modules.name == module_name) &
        (db.community_members.community_id == db.communities.id) &
        (db.community_members.identity_id == db.identities.id) &
        (db.roles.id == db.community_members.role_id)
    )
    fields = (
        db.communities.ALL,
        db.identities.ALL,
        db.modules.ALL,
        db.roles.name.with_alias('role_name')
    )
    return db(query).select(*fields).first()

# Install a community module, using its module_id in a payload, into a given community_name as an argument. If the community module already exists in the given community, return an error.
@action(base_route + "install_by_community_name", method="POST")
@action.uses(db)
@basic_auth(auth)
def install_by_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    community_name = community.community_name
    identity = payload['identity']
    identity_name = identity.name
    command_str_list = payload['command_string']

    if not command_str_list:
        return dict(msg="No command string provided.", error=True, status=400)
    
    # Set the module_name to the first element in the command_str_list
    module_name = command_str_list[0]

    # Combine queries for community, identity, and module
    result = get_lookup(community_name, identity_name, module_name)
    if not result:
        return dict(msg="Invalid community, identity, or module, or identity is not a member of the community.")

    if result.communities.community_name == "Global":
        return dict(msg="Cannot install community module in Global community.")

    if result.role_name not in ['Admin', 'Owner', 'admin', 'owner']:
        return dict(msg="Identity is not an admin of the community.")

    module_type = db(db.module_types.id == result.modules.module_type_id).select(db.module_types.name).first()
    if module_type.name != "Community":
        return dict(msg="This operation is only allowed for Community modules.")

    existing_module = db((db.community_modules.community_id == result.communities.id) & 
                         (db.community_modules.module_id == result.modules.id)).select().first()
    if existing_module:
        return dict(msg="This module is already installed in this community.")

    new_module = {
        'module_id': result.modules.id,
        'community_id': result.communities.id,
        'enabled': True,
        'privilages': ['read', 'write', 'execute']
    }
    db.community_modules.insert(**new_module)
    return dict(msg="Community module installed.")

# Uninstall a community module, using its module_id in a payload, from a given community_name as an argument. If the community module does not exist in the given community, return an error.
@action(base_route + "uninstall_by_community_name", method="DELETE")
@action.uses(db)
@basic_auth(auth)
def uninstall_by_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    community_name = community.community_name
    identity = payload['identity']
    identity_name = identity.name
    command_str_list = payload['command_string']

    if not command_str_list:
        return dict(msg="No command string provided.", error=True, status=400)
    
    # Set the module_name to the first element in the command_str_list
    module_name = command_str_list[0]
    
    # Combine queries for community, identity, and module
    result = get_lookup(community_name, identity_name, module_name)
    if not result:
        return dict(msg="Invalid community, identity, or module, or identity is not a member of the community.")

    if result.communities.community_name == "Global":
        return dict(msg="Cannot uninstall community module in Global community.")

    if result.role_name not in ['Admin', 'Owner', 'admin', 'owner']:
        return dict(msg="Identity is not an admin of the community.")

    # Check that the module exists
    community_module = db((db.community_modules.community_id == result.communities.id) & (db.community_modules.module_id == result.modules.id)).select().first()
    
    if not community_module:
        return dict(msg="Community module does not exist.")

    community_module.delete_record()
    return dict(msg="Community module uninstalled.")
