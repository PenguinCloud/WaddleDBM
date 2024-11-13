# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from roles.py")

# Create a new role from a given payload. Throws an error if no payload is given, or the role already exists.
def create_role():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)

    needed_fields = ['name', 'description', 'priv_list', 'requirements', 'community_name']

    if not all(field in payload for field in needed_fields):
        return dict(msg=f"Payload missing required fields. Required fields are: {needed_fields}")
    
    # Get the community by name
    community = waddle_helpers.get_community_record_by_name(payload['community_name'])

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
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    role = db(db.roles.name == name).select().first()
    return dict(msg="Role does not exist.") if not role else dict(data=role)

# Get a role by community name. If the role does not exist, return an error.
def get_by_community_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
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

# Set the role of a given identity by its name and community name. If the role does not exist, return an error.
# The function accepts 2 identity names, a role name, and a community name. The first identity is the identity
# whose role is to be set, and the second identity is the identity of the user making the request.
# Only an identity with admin privileges can set the role of another identity.
def set_role():
    # Check if there is a request argument. If not, return an error.
    re = request.args(0)
    if not re:
        return dict(msg="No community name given in the URL path.")
    
    # Check if the community exists. If not, return an error.
    community_name = re
    community = waddle_helpers.get_community(community_name)

    if not community:
        return dict(msg="Community does not exist.")

    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    
    payload = jloads(payload)

    required_fields = ['identity_name', 'role_name', 'role_receiver']

    if not all(field in payload for field in required_fields):
        return dict(msg=f"Payload missing required fields. Required fields are: {required_fields}")
    
    identity_name = payload['identity_name']
    role_name = payload['role_name']
    role_receiver_name = payload['role_receiver']
    
    # Get the role by name and community id
    role = db((db.roles.name == role_name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Get the role_receiver identity by name
    role_receiver = waddle_helpers.get_identity(role_receiver_name)
    if not role_receiver:
        return dict(msg="Identity does not exist.")
    
    # Check that the receiver is in the community
    if not waddle_helpers.identity_in_community(role_receiver_name, community_name):
        return dict(msg="Identity is not in the community.")
    
    # Get the identity of the requester
    requester = waddle_helpers.get_identity(identity_name)
    if not requester:
        return dict(msg="Requester does not exist.")
    
    # Check if the requester has admin privileges
    if not waddle_helpers.identity_is_admin(identity_name, community_name):
        return dict(msg="Requester does not have admin privileges.")
    
    # Set the role of the identity
    message = waddle_helpers.set_role(role_receiver, role, community)
    return dict(msg=message)

# Update a role by a given payload name and community name. If the role does not exist, return an error.
def update_by_name_and_community_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")

    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)

    required_fields = ['name', 'description', 'priv_list', 'requirements', 'community_name']

    if not all(field in payload for field in required_fields):
        return dict(msg="Payload missing required fields. Required fields are: name, description, priv_list, requirements, community_name")
    
    # Get the community by name
    community = waddle_helpers.get_community_record_by_name(payload['community_name'])
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
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
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
    name = waddle_helpers.decode_name(name)
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
    
    payload = jloads(payload)

    required_fields = ['name', 'community_name']

    if not all(field in payload for field in required_fields):
        return dict(msg=f"Payload missing required fields. Required fields are: {required_fields}")
    
    name = payload['name']
    community_name = payload['community_name']
    
    # Get the community by name
    community = waddle_helpers.get_community_record_by_name(community_name)
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the role by name and community id
    role = db((db.roles.name == name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Set the role of all identities in the community to the default "Member" role
    waddle_helpers.set_default_role_for_identities_in_community(community.id, role.id)

    # Delete the role
    role.delete_record()

    return dict(msg="Role deleted.")