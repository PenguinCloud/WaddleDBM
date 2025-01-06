# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from communities.py")

# Create a new community member from a given payload. Throws an error if no payload is given, or the community member id already exists in a given community id
def create_member():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Get the identity_id from the identities table, using the identity_name, if it exists.
    identity = db(db.identities.name == identity.name).select().first()
    if not identity:
        return dict(msg="Identity does not exist.", status=400)

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]

    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()

    if not community:
        return dict(msg="Community does not exist.", status=400)
    
    # Set the default role_id to that of a Member in the roles table.
    role_id = waddle_helpers.get_member_role_id(community.id)
    if not role_id:
        return dict(msg="Member role does not exist.", status=400)

    # Check if the community member already exists in the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if community_member:
        return dict(msg="Community member already exists.")

    # Create the community member.
    db.community_members.insert(community_id=community.id, identity_id=identity.id, role_id=role_id)

    return dict(msg=f"{identity.name} has joined the community {community_name}.")

# Get all community members accross all communities.
def get_all():
    community_members = db(db.community_members).select()
    return dict(data=community_members, status=200)

# Get community members by a given community name. Return the member names, as well as their roles. If the community does not exist, return an error.
def get_names_by_community_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']

    community_members = db(db.community_members.community_id == community.id).select()
    community_members = [{"name": member.identity_id.name, "role": member.role_id.name} for member in community_members]
    return dict(data=community_members)

# Using the community name and identity name, remove a member from a community.
def remove_member():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the community name to the first element of the command string.
    community_name = command_str_list[0]
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")

    # Get the identity_id from the identities table, using the identity_name, if it exists.
    if not identity:
        return dict(msg="Identity does not exist.")

    # Check if the community member already exists in the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Community member does not exist.")

    # If the given community is Global, return an error, because no member can leave the Global community.
    if community.community_name == "Global":
        return dict(msg="Cannot leave the Global community.")

    # Remove the community member.
    community_member.delete_record()

    # If there is only one member left of the community and the last member does not have the Owner role, give the last member the Owner role. Include a message that the Owner role has been given to the last member.
    msg = f"{identity.name} has left the community {community_name}."
    community_members = db(db.community_members.community_id == community.id).select()
    if len(community_members) > 0:
        owner_role = db(db.roles.name == "Owner").select().first()
        if owner_role:
            community_members[0].update_record(role_id=owner_role.id)
            msg += f" The Owner role has been given to {community_members[0].identity_id.name}."

    return dict(msg=f"{identity.name} has left the community {community_name}.")

# Using a community name, identity name, member name and role name, update the role of a member in a community to the given role, if the member exists, the role exists, the community exists, the identity exists, and the identity is the owner of the community.
def update_member_role():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the member name to the first element of the command string.
    member_name = command_str_list[0]

    # Set the role name to the second element of the command string.
    role_name = command_str_list[1]

    # Get the member_id from the identities table, using the member_name, if it exists.
    member = db(db.identities.name == member_name).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Get the role_id from the roles table, using the role_name, if it exists.
    role = db(db.roles.name == role_name).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Get the Owner role from the roles table.
    owner_role = db(db.roles.name == "Owner").select().first()
    if not owner_role:
        return dict(msg="Owner role does not exist.")

    # Check if the identity is the owner of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg=f"{identity.name} is not a member of the community.")
    if community_member.role_id != owner_role.id:
        return dict(msg=f"{identity.name} is not the owner of the community.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    # Update the role of the member.
    community_member.update_record(role_id=role.id)

    return dict(msg=f"{member_name}'s role has been updated to {role_name}.")
