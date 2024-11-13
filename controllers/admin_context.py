# -*- coding: utf-8 -*-
from json import loads as jloads
from datetime import datetime, timedelta
from uuid import uuid4
from threading import Thread
from time import sleep
import logging

# Set logging level to INFO
logging.basicConfig(level=logging.INFO)

# try something like
def index(): return dict(message="hello from admin_context.py")

# Function to create a new admin context session for a given community name and identity name found in a payload.
# Throws an error if no payload is given, or the community or identity does not exist. The identity must also be an admin or owner of the community.
def create_session():
    # Get the community name from the arguments.
    community_name = request.args(0)
    if not community_name:
        return dict(msg="No community name given.")
    
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = loads(payload)

    # Check if the payload contains the required fields.
    if 'identity_name' not in payload:
        return dict(msg="Payload missing required fields. Please provide the identity name.", error=True)
    
    # Check if the community exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community not found.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity not found.")
    
    # From the community members table, check if the given identity is part of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not part of the community.")
    
    # Using the role_id from the community member, check if the identity is an admin or owner in the roles table.
    role = db((db.roles.id == community_member.role_id)).select().first()
    required_privileges = ['Admin', 'Owner', 'admin', 'owner']

    role_privileges = role.priv_list

    # Check if the role privileges are in the required privileges list.
    if not any(privilege in role_privileges for privilege in required_privileges):
        return dict(msg="Identity is not an admin or owner of the community.")
    
    # Set a session expiration time of 1 hour.
    expiration_time = datetime.now() + timedelta(hours=1)

    # Generate a unique session ID token.
    session_token = str(uuid4())

    # If an admin context session already exists for the community and identity, update the session expiration time.
    admin_context = db((db.admin_contexts.community_id == community.id) & (db.admin_contexts.identity_id == identity.id)).select().first()
    if admin_context:
        admin_context.update_record(session_token=session_token, session_expires=expiration_time)
        return dict(msg="Admin context session updated.", session_token=session_token)

    # Insert the new session into the admin_contexts table.
    db.admin_contexts.insert(session_token=session_token, community_id=community.id, identity_id=identity.id, session_expires=expiration_time)

    return dict(msg="Admin context session created.", session_token=session_token)

# Function to get an admin context session by its session token. If the session does not exist, return an error.
def get_by_session_token():
    session_token = request.args(0)
    admin_context = db(db.admin_contexts.session_token == session_token).select().first()
    if not admin_context:
        return dict(msg="Admin context session not found.")
    return dict(data=admin_context)

# Function to get an admin session by a given community name and identity name in a payload. If the session does not exist, return an error.
def get_by_community_and_identity():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = loads(payload)

    # Check if the payload contains the required fields.
    if 'community_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community not found.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity not found.")
    
    # From the community members table, check if the given identity is part of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not part of the community.")
    
    # Using the role_id from the community member, check if the identity is an admin or owner in the roles table.
    role = db(db.roles.id == community_member.role_id).select().first()
    if role.name not in ['Admin', 'Owner']:
        return dict(msg="Identity is not an admin or owner of the community.")
    
    # Check if the admin context session exists.
    admin_context = db((db.admin_contexts.community_id == community.id) & (db.admin_contexts.identity_id == identity.id)).select().first()
    if not admin_context:
        return dict(msg="Admin context session not found.")
    return dict(data=admin_context)

# Function to refresh an admin context session by its session token. If the session does not exist, return an error.
def refresh_by_session_token():
    session_token = request.args(0)
    admin_context = db(db.admin_contexts.session_token == session_token).select().first()
    if not admin_context:
        return dict(msg="Admin context session not found.")
    
    # Set a new session expiration time of 1 hour from now.
    expiration_time = datetime.now() + timedelta(hours=1)
    admin_context.update_record(session_expires=expiration_time)

    return dict(msg="Admin context session refreshed.")

# From a given community name, identity name and module id in a payload, get the admin session context using the 
# community and identity. If a session exists, check if the module is part of the community. If the module is part of the community,
# return the admin session context. If the module is not part of the community, return an error. Each message will return an error flag
# to indicate whether the operation was successful or not.
def check_module_in_community():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = loads(payload)

    # Check if the payload contains the required fields.
    if 'community_name' not in payload or 'identity_name' not in payload or 'module_id' not in payload:
        return dict(msg="Payload missing required fields. Please provide the community name, identity name, and module ID.", error=True)
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community not found.", error=True)
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity not found.", error=True)
    
    # From the community members table, check if the given identity is part of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not part of the community.", error=True)
    
    # Using the role_id from the community member, check if the identity is an admin or owner in the roles table.
    role = db(db.roles.id == community_member.role_id).select().first()
    if role.name not in ['Admin', 'Owner']:
        return dict(msg="Identity is not an admin or owner of the community.", error=True)
    
    # Check if the admin context session exists.
    admin_context = db((db.admin_contexts.community_id == community.id) & (db.admin_contexts.identity_id == identity.id)).select().first()
    if not admin_context:
        return dict(msg="Admin session not found. Please log in to the community first.", error=True)
    
    # Check if the module exists in the community.
    module = db((db.community_modules.community_id == community.id) & (db.community_modules.id == payload['module_id'])).select().first()
    if not module:
        return dict(msg="Module not found in the current community. Please check if the module is installed in the current community, or log into the correct community.", error=True)
    
    return dict(data=admin_context, error=False)

# Function to delete an admin context session by a given community name in the arguments and an identity name in a payload. 
# If the session does not exist, return an error.
def delete_by_community_and_identity():
    community_name = request.args(0)
    if not community_name:
        return dict(msg="No community name given.")
    
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)

    # Check if the payload contains the required fields.
    if 'identity_name' not in payload:
        return dict(msg="Payload missing required fields. Please provide the identity name.", error=True)
    
    # Check if the community exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community not found.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity not found.")
    
    # From the community members table, check if the given identity is part of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not part of the community.")
    
    # Using the role_id from the community member, check if the identity is an admin or owner in the roles table.
    role = db((db.roles.id == community_member.role_id)).select().first()
    required_privileges = ['Admin', 'Owner', 'admin', 'owner']

    role_privileges = role.priv_list

    # Check if the role privileges are in the required privileges list.
    if not any(privilege in role_privileges for privilege in required_privileges):
        return dict(msg="Identity is not an admin or owner of the community.")
    
    # Check if the admin context session exists.
    admin_context = db((db.admin_contexts.community_id == community.id) & (db.admin_contexts.identity_id == identity.id)).select().first()
    if not admin_context:
        return dict(msg="Admin context session not found.")
    
    admin_context.delete_record()
    return dict(msg="Admin context session deleted.")

# Function to delete an admin context session by its session token. If the session does not exist, return an error.
def delete_by_session_token():
    session_token = request.args(0)
    admin_context = db(db.admin_contexts.session_token == session_token).select().first()
    if not admin_context:
        return dict(msg="Admin context session not found.")
    admin_context.delete_record()
    return dict(msg="Admin context session deleted.")

# Function to delete all expired admin context sessions. This function is called periodically by a scheduler.
def delete_expired_sessions():
    current_time = datetime.now()
    db(db.admin_contexts.session_expires < current_time).delete()
    logging.info("Expired admin context sessions deleted.")
    return dict(msg="Expired admin context sessions deleted.")

# Function to continuously delete expired admin context sessions every 5 minutes.
def delete_expired_sessions_continuously():
    while True:
        delete_expired_sessions()
        sleep(300)

# Function to start a thread that continuously deletes expired admin context sessions.
def start_delete_expired_sessions_thread():
    thread = Thread(target=delete_expired_sessions_continuously)
    thread.start()
    return dict(msg="Thread started.")