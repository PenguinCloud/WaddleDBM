# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from roles.py")

# Create a new role from a given payload. Throws an error if no payload is given, or the role already exists.
def create_role():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the command string elements as follows into an insert dictionary:
    # name: command_str_list[0]
    # description: command_str_list[1]
    # priv_list: command_str_list[2]
    # requirements: command_str_list[3]
    # community_name: command_str_list[4]
    insert_dict = {
        'name': command_str_list[0],
        'description': command_str_list[1],
        'priv_list': command_str_list[2],
        'requirements': command_str_list[3],
        'community_name': command_str_list[4]
    }

    # Check if the identity is an admin of the community
    if not waddle_helpers.identity_is_admin(identity.name, community.community_name):
        return dict(msg="Identity is not an admin of the community.")
    
    # Check if the role already exists for the community
    role = db((db.roles.name == insert_dict["name"]) & (db.roles.community_id == community.id)).select().first()
    if role:
        return dict(msg="Role already exists.")
    
    db.roles.insert(insert_dict)
    return dict(msg="Role created.")

# Get all roles.
def get_all():
    roles = db(db.roles).select()
    return dict(data=roles)

# Function to get the role that is allocated to a given identity in a given community.
def get_role_by_identity_and_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    
    identity_name = identity.name
    community_name = community.community_name
    
    # Check if the identity is in the community
    if not waddle_helpers.identity_in_community(identity_name, community_name):
        return dict(msg="Identity is not in the community.")
    
    role = waddle_helpers.get_identity_role_in_community(identity_name, community_name)
    return dict(data=role)

# Get a role by its name. If the role does not exist, return an error.
def get_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    command_str_list = payload['command_string']

    # Set the role name to the first element of the command string.
    role_name = command_str_list[0]

    if not name:
        return dict(msg="No name given.")
    role = db(db.roles.name == name).select().first()
    return dict(msg="Role does not exist.") if not role else dict(data=role)

# Get a role by community name. If the role does not exist, return an error.
def get_by_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']

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
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    identity_name = identity.name
    command_str_list = payload['command_string']
    
    # Get the role name and role receiver name from the command string's first and second elements
    role_name = command_str_list[0]
    role_receiver_name = command_str_list[1]
    
    # Get the role by name and community id
    role = db((db.roles.name == role_name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Get the role_receiver identity by name
    role_receiver = waddle_helpers.get_identity(role_receiver_name)
    if not role_receiver:
        return dict(msg="Identity does not exist.")
    
    # Check that the receiver is in the community
    if not waddle_helpers.identity_in_community(role_receiver_name, community.name):
        return dict(msg="Identity is not in the community.")
    
    # Get the identity of the requester
    requester = waddle_helpers.get_identity(identity_name)
    if not requester:
        return dict(msg="Requester does not exist.")
    
    # Check if the requester has admin privileges
    if not waddle_helpers.identity_is_admin(identity_name, community.name):
        return dict(msg="Requester does not have admin privileges.")
    
    # Set the role of the identity
    message = waddle_helpers.set_role(role_receiver, role, community)
    return dict(msg=message)

# Update a role by a given payload name and community name. If the role does not exist, return an error.
def update_by_name_and_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the command string elements as follows into an insert dictionary:
    # name: command_str_list[0]
    # description: command_str_list[1]
    # priv_list: command_str_list[2]
    # requirements: command_str_list[3]
    # community_name: command_str_list[4]
    insert_dict = {
        'name': command_str_list[0],
        'description': command_str_list[1],
        'priv_list': command_str_list[2],
        'requirements': command_str_list[3],
        'community_name': command_str_list[4]
    }
    
    role = db((db.roles.name == insert_dict["name"]) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")

    # Check that the identity is an admin of the community
    if not waddle_helpers.identity_is_admin(identity.name, community.community_name):
        return dict(msg="Identity is not an admin of the community.")

    role.update_record(**insert_dict)
    return dict(msg="Role updated.")

# Delete a role by its name. If the role does not exist, return an error.
def delete_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    command_str_list = payload['command_string']

    # Set the role name to the first element of the command string.
    name = command_str_list[0]

    role = db(db.roles.name == name).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    role.delete_record()
    return dict(msg="Role deleted.") 

# Delete a role by its name and community name. If the role does not exist, return an error.
# If the role is deleted, set the role of all identities in the community to the default "Member" role.
def delete_by_name_and_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the role name to the first element of the command string.
    name = command_str_list[0]
    
    # Get the role by name and community id
    role = db((db.roles.name == name) & (db.roles.community_id == community.id)).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Set the role of all identities in the community to the default "Member" role
    waddle_helpers.set_default_role_for_identities_in_community(community.id, role.id)

    # Delete the role
    role.delete_record()

    return dict(msg="Role deleted.")