# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from roles.py")

# Function to decode names with special characters in them.
from urllib.parse import unquote

def decode_name(name):
    return unquote(name) if name else None

# Helper function to get a community record by its name.
def get_community_record_by_name(name):
    return db(db.communities.community_name == name).select().first()

# Helper function to get an identity record by its name.
def get_identity_record_by_name(name):
    return db(db.identities.name == name).select().first()

# Helper function to set the role of all identities in a community to the default "Member" role when a role is deleted.
# Only identities with the deleted role are affected.
def set_default_role_for_identities_in_community(community_id, role_id):
    db(
        (db.community_members.community_id == community_id) &
        (db.community_members.role_id == role_id)
    ).update(role_id=DEFAULT_ROLE_ID)
    identities = db(db.community_members.community_id == community_id).select()

    if identities:
        for identity in identities:
            if identity.role_id == role_id:
                identity.update_record(role_id=1)

# Create a new role from a given payload. Throws an error if no payload is given, or the role already exists.
def create_role():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)

    needed_fields = ['name', 'description', 'priv_list', 'requirements', 'community_name']

    if not all(field in payload for field in needed_fields):
        return dict(msg=f"Payload missing required fields. Required fields are: {needed_fields}")
    
    # Get the community by name
    community = get_community_record_by_name(payload['community_name'])

    # Check if the community exists
    if not community:
        return dict(msg="Community does not exist.")
    
    payload['community_id'] = community.id
    
    # Check if the role already exists for the community
    role = db((db.roles.name == payload['name']) & (db.roles.community_id == community.id)).select().first()
    if role:
        return dict(msg="Role already exists.")
    
    db.roles.insert(**payload)
    return dict(msg="Role created.")

# Get all roles.
def get_all():
    roles = db(db.roles).select()
    return dict(data=roles)

# Get a role by its name. If the role does not exist, return an error.
def get_by_name():
    name = request.args(0)
    name = decode_name(name)
    if not name:
        return dict(msg="No name given.")
    role = db(db.roles.name == name).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    return dict(data=role)

# Get a role by community name. If the role does not exist, return an error.
def get_by_community_name():
    name = request.args(0)
    name = decode_name(name)
    if not name:
        return dict(msg="No name given.")
    
    # Get the community by name
    community = db(db.communities.community_name == name).select().first()
    if not community:
        return dict(msg="Community does not exist.")

    role = db(db.roles.community_id == community.id).select()
    if not role:
        return dict(msg="Role does not exist.")
    else:
        return dict(data=role)

# Update a role by a given payload name and community name. If the role does not exist, return an error.
def update_by_name_and_community_name():
    name = request.args(0)
    name = decode_name(name)
    if not name:
        return dict(msg="No name given.")

    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)

    required_fields = ['name', 'description', 'priv_list', 'requirements', 'community_name']

    if not all(field in payload for field in required_fields):
        return dict(msg="Payload missing required fields. Required fields are: name, description, priv_list, requirements, community_name")
    
    # Get the community by name
    community = get_community_record_by_name(payload['community_name'])
    if not community:
        return dict(msg="Community does not exist.")
    
    # Set the community id in the payload
    payload['community_id'] = community.id
    
    role = db((db.roles.name == name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")

    role.update_record(**payload)
    return dict(msg="Role updated.")

# Update a role by its name. If the role does not exist, return an error.
def update_by_name():
    name = request.args(0)
    name = decode_name(name)
    if not name:
        return dict(msg="No name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'name' not in payload or 'description' not in payload or 'priv_list' not in payload or 'requirements' not in payload:
        return dict(msg="Payload missing required fields.")
    role = db(db.roles.name == name).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    role.update_record(**payload)
    return dict(msg="Role updated.")

# Delete a role by its name. If the role does not exist, return an error.
def delete_by_name():
    name = request.args(0)
    name = decode_name(name)
    if not name:
        return dict(msg="No name given.")
    role = db(db.roles.name == name).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    role.delete_record()
    return dict(msg="Role deleted.") 

# Delete a role by its name and community name. If the role does not exist, return an error.
# If the role is deleted, set the role of all identities in the community to the default "Member" role.
def delete_by_name_and_community_name():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    required_fields = ['name', 'community_name']

    if not all(field in payload for field in required_fields):
        return dict(msg=f"Payload missing required fields. Required fields are: {required_fields}")
    
    name = payload['name']
    community_name = payload['community_name']
    
    # Get the community by name
    community = get_community_record_by_name(community_name)
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the role by name and community id
    role = db((db.roles.name == name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Set the role of all identities in the community to the default "Member" role
    set_default_role_for_identities_in_community(community.id, role.id)

    # Delete the role
    role.delete_record()

    return dict(msg="Role deleted.")