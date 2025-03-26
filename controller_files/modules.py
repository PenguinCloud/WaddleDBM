# -*- coding: utf-8 -*-
from json import loads as jloads
from urllib.parse import unquote
import logging
import os

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..modules.auth_utils import basic_auth

# Define the base route for the marketplace controller
base_route = "api/modules/"

# try something like
def index(): return dict(message="hello from modules.py")

# Function to decode names with space in
from urllib.parse import unquote

def decode_name(name: str) -> str:
    outName = unquote(name)

    # If the name contains a _ character, replace it with a space
    if "_" in outName:
        outName = outName.replace("_", " ")

    return outName

# Helper function to get a record from a given table, field and value
def get_db_record(table, field, value):
    return db(table[field] == value).select().first()

# Helper function to raplace all spaces in given command string with _ and return the new string
def replace_spaces(command):
    return command.replace(" ", "_")

# A helper function to return an identity record from a given identity_name
def get_identity_record(identity_name: str):
    return db(db.identities.name == identity_name).select().first()

# A helper function to return a community record from a given community_name
def get_community_record_by_id(community_id: int):
    return db(db.communities.id == community_id).select().first()

# A helper function to get the current community context of a given identity_name
def get_community_context(identity_name: str):
    identity = get_identity_record(identity_name)
    # If the identity does not exist, return None. Else, return the community context of the identity.
    if identity is None:
        return None
    else:
        return db(db.context.identity_id == identity.id).select().first()

# A helper function to return a given identity_name as a community member from a community name
def get_community_member(identity_name: str, community_id: int):
    identity = get_identity_record(identity_name)
    community = get_community_record_by_id(community_id)

    if identity and community:
        return db((db.community_members.identity_id == identity.id) & (db.community_members.community_id == community.id)).select().first()
    
    return None
        
    
# A helper function to use a given identity_name and retrieve a list of priv_list that the identity has in a given community, according to the community context.
def get_priv_list(identity_name: str) -> list:
    community_context = get_community_context(identity_name)
    if not community_context:
        return None

    community_member = get_community_member(identity_name, community_context.community_id)
    if not community_member:
        return None

    role = get_db_record(db.roles, 'id', community_member.role_id)
    return role.priv_list if role else None
        
# A helper function to get an admin context session by a given identity name. The identity name is used to derive the current community context of the identity.
# Returns an admin context session if one exists for the identity and the identity is an admin of the community context. Else, returns None.
def get_admin_context_session(identity_name: str):
    community_context = get_community_context(identity_name)
    if community_context is None:
        return None
    else:
        community_id = community_context.community_id
        community_member = get_community_member(identity_name, community_id)

        if community_member is None:
            return None
        else:
            role = db((db.roles.community_id == community_context.community_id) & (db.roles.id == community_member.role_id)).select().first()

            if role:
                if 'admin' in role.priv_list:
                    return db((db.admin_contexts.community_id == community_id) & (db.admin_contexts.identity_id == community_member.identity_id)).select().first()

    return None
                
# A helper function to get an alias value by a given alias value and identity name. The identity name is used to derive the current community context of the identity.
# Returns an alias value if one exists for the community. Else, returns None.
def get_alias_command(alias, identity_name):
    community_context = get_community_context(identity_name)
    if community_context is None:
        return None
    community_id = community_context.community_id
    return (
        db(
            (db.alias_commands.community_id == community_id)
            & (db.alias_commands.alias_val == alias)
        )
        .select()
        .first()
    )
    
# A helper function to get a marketplace module by a given command, as a result of a given alias. 
# The identity name is used to derive the current community context of the identity.
# Returns a marketplace module if one exists for the community. Else, returns None.
def get_marketplace_module_by_alias(alias, identity_name):
    alias_command = get_alias_command(alias, identity_name)
    print(f"Alias command: {alias_command}")
    if alias_command is None:
        return None
    else:
        return (
            db(
                (
                    db.module_commands.command_name == alias_command.command_val
                )
            )
            .select()
            .first()
        )

# Decorator to require a payload in the request body. If no payload is given, return an error message.
def require_payload(f):
    def wrapper(*args, **kwargs):
        raw_payload = request.body.read()
        if not raw_payload:
            return dict(msg="No payload given.")
        payload = jloads(raw_payload)
        return f(payload, *args, **kwargs)
    return wrapper

# Create a new marketplace module from a given payload. Throws an error if no payload is given, or the marketplace module already exists.
@require_payload
def create(payload):
    if not all(field in payload for field in ('name', 'description', 'gateway_url', 'module_type_id', 'metadata')):
        return dict(msg="Payload missing required fields.")
    if db(db.modules.name == payload['name']).count() > 0:
        return dict(msg="Marketplace Module already exists.")
    db.modules.insert(**payload)
    return dict(msg="Marketplace Module created.")

# Get a marketplace module by name. Throws an error if no name is given, or the marketplace module does not exist.
# An identity name must be present in the payload to also return the available roles for the identity in the community context.
# If the marketplace module does not exist, check if the name can be used as an alias to get the marketplace module.
# If the alias command exists, return the aliased command value.
@require_payload
def get(payload):
    # Check if the payload contains the required fields
    if 'name' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields.")
    
    identity_name = payload["identity_name"]
    name = payload["name"]

    if identity_name:
        # Get the marketplace module. If it does not exists, check if the name can be used as an alias to get the marketplace module.
        # If the marketplace module still does not exist, return an error.
        marketplace_module = db(db.modules.name == name).select().first()

        aliased_command = None

        if not marketplace_module:
            marketplace_module = get_marketplace_module_by_alias(name, identity_name)
            if marketplace_module:
                aliased_command = get_alias_command(name, identity_name)
            else:
                return dict(msg="Marketplace Module does not exist.", status=404)
        
        # Also return the marketplace module type name part of the response
        module_type = db(db.module_types.id == marketplace_module.module_type_id).select().first()
        marketplace_module = marketplace_module.as_dict()
        marketplace_module['module_type_name'] = module_type.name

        # Get the available priv_list for the identity in the community context
        priv_list = get_priv_list(identity_name)
        marketplace_module['priv_list'] = priv_list

        # Get the admin context session for the identity
        admin_context_session = get_admin_context_session(identity_name)
        marketplace_module['session_data'] = admin_context_session or None

        # If the alias command exists, return the aliased command value
        if aliased_command:
            marketplace_module['aliased_command'] = aliased_command.command_val
        
        return marketplace_module
    else:
        return dict(msg="No identity name given.")

# Get all marketplace modules.
def get_all():
    modules = db(db.modules).select()
    # Add the module type name to each marketplace module
    for marketplace_module in modules:
        module_type = db(db.module_types.id == marketplace_module.module_type_id).select().first()
        marketplace_module.module_type_name = module_type.name
    return dict(data=modules)

# Function to get all module commands from the module_commands table
@action(base_route + "get_all_module_commands", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_all_module_commands():
    commands = db(db.module_commands).select()
    return dict(data=commands)

# Get all the marketplace modules, as only the name and the id. Only modules that fall under the Community module type are returned.
@action(base_route + "get_all_community_modules", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_all_community_modules():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    
    payload = jloads(payload)
    module_type = payload.get("module_type", "Community")
    
    module_type_record = db(db.module_types.name == module_type).select().first()
    if not module_type_record:
        return dict(msg=f"Module type '{module_type}' not found.")
    
    modules = db(db.modules.module_type_id == module_type_record.id).select(
        db.modules.id, db.modules.name
    )
    return dict(data=modules)

# Remove a marketplace module by name. Throws an error if no name is given, or the marketplace module does not exist.
def remove():
    name = decode_name(request.args(0))
    if not name:
        return dict(msg="No name given.")
    marketplace_module = db(db.modules.name == name).select().first()
    if not marketplace_module:
        return dict(msg="Marketplace Module does not exist.")
    db(db.modules.name == name).delete()
    return dict(msg="Marketplace Module removed.")

# Update a marketplace module by name. Throws an error if no name is given, or the marketplace module does not exist.
@require_payload
def update():
    name = decode_name(request.args(0))
    if not name:
        return dict(msg="No name given.")
    marketplace_module = db(db.modules.name == name).select().first()
    if not marketplace_module:
        return dict(msg="Marketplace Module does not exist.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    marketplace_module.update_record(**payload)
    return dict(msg="Marketplace Module updated.")

# Function to output the URL of the module onboarding page.
@action(base_route + "start_module_onboard", method="GET")
@action.uses(db)
@basic_auth(auth)
def start_module_onboard():
    onboardUrl = os.environ.get("MODULE_ONBOARD_URL")
    return dict(msg=f"Thank you for choosing Waddlebot! If you wish to onboard a new module, please visit the following URL: {onboardUrl}")
