# -*- coding: utf-8 -*-
from json import loads as jloads

# try something like
def index(): return dict(message="hello from communities.py")

# Create a new community from a given payload. Throws an error if no payload is given, or the community already exists.
def create():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)
    
    command_str_list = payload['command_string']

    # Set the community name and description to the first and second elements of the command string, respectively.
    community_name = command_str_list[0]
    community_description = command_str_list[1]

    # Check if the community already exists.
    if db(db.communities.community_name == community_name).count() > 0:
        return dict(msg="Community already exists.", error=True, status=400)
    db.communities.insert(community_name=community_name, community_description=community_description)
    return dict(msg="Community created.", status=200)

# Create a new community with a payload only containing the community name. Throws an error if no payload is given, or the community already exists.
def create_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]

    community_description = ""

    # Set the community description to the second element of the command string, if there is one.
    if len(command_str_list) > 1:
        community_description = command_str_list[1]

    # Check if the community already exists.
    if db(db.communities.community_name == community_name).count() > 0:
        return dict(msg="Community already exists.")
    
    # Create the community with the given community name.
    db.communities.insert(community_name=community_name, community_description=community_description)

    # Create the default roles for the community, using the community_id of the newly created community, as well as the
    # the db_initialization.py file's create_roles function.
    db_init.create_roles(community.id)

    # From the roles table, get the Owner role for the community.
    role = waddle_helpers.get_owner_role(community.id)
    db.community_members.insert(community_id=community.id, identity_id=identity.id, role_id=role.id, currency=0)

    return dict(msg="Community created. You have been granted the Owner role of this community.")

# Get all communities.
def get_all():
    communities = db(db.communities).select()
    return dict(data=communities)

# Get a community by its name. If the community does not exist, return an error.
def get_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)

    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]

    if not community_name:
        return dict(msg="No community name given.", error=True, status=400)
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)
    
    return dict(data=community, status=200)

# Update a community by its name. If the community does not exist, return an error.
def update_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]

    # Set the community description to the second element of the command string, if there is one.
    community_description = command_str_list[1]

    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)
    
    community.update_record(community_name=community_name, community_description=community_description)
    return dict(msg="Community updated.", status=200)

# Update a community's description by its name. This can only be done by an identity_name that is part of the community with the Owner role. If the community does not exist, return an error.
def update_desc_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)
    
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]

    # Set the community description to the second element of the command string, if there is one.
    community_description = command_str_list[1]

    if not community_name:
        return dict(msg="No community name given.", error=True, status=400)
    
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)

    member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not member:
        return dict(msg="You are not a member of this community.")
    role = db(db.roles.id == member.role_id).select().first()
    if role.name != "Owner":
        return dict(msg="You do not have permission to update this community's description.", error=True, status=400)
    community.update_record(community_description=community_description)
    return dict(msg="Community description updated.", status=200)
    

# Delete a community by its name. This can only be done by an identity_name that is part of the community with the Owner role. If the community does not exist, return an error. 
def delete_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True)
    
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]
    
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)

    member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not member:
        return dict(msg="You are not a member of this community.", error=True, status=400)
    
    role = db(db.roles.id == member.role_id).select().first()
    if role.name != "Owner":
        return dict(msg="You do not have permission to delete this community.", error=True, status=400)
    
    db(db.communities.community_name == community_name).delete()
    return dict(msg="Community deleted.", status=200)

    
