# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from communities.py")

# Function to decode names with space in
def decode_name(name):
    if not name:
        return None
    name = name.replace("%20", " ")
    name = name.replace("_", " ")

    return name

# A helper function to create a list of roles for a newly created community, using its community_id.
# TODO: Figure out how to add the requirements field to the roles table and implement it.
def create_roles(community_id):
    roles = ['Member', 'Admin', 'Owner']

    requirements = ["None"]

    for role in roles:
        privilages = []
        description = ""

        # If the role is member, set the privilages to read only.
        if role == "Member":
            privilages = ["read"]
            description = "This role is the default role for all members of the community. Members can only read data from the community."
        # Else, if the role is admin, set the privilages to read, write and admin.
        elif role == "Admin":
            privilages = ["read", "write", "admin"]
            description = "This role is for community admins. Admins can read, write and admin the community."
        # Else, if the role is owner, set the privilages to read, write, update, delete, admin and owner.
        elif role == "Owner":
            privilages = ["read", "write", "update", "delete", "admin", "owner"]
            description = "This role is for the owner of the community. Owners can read, write, update, delete, admin and owner the community."

        db.roles.insert(name=role, description=description, community_id=community_id, privilages=privilages, requirements=requirements)

# Get the owner role for a given community_id.
def get_owner_role(community_id):
    role = db((db.roles.community_id == community_id) & (db.roles.name == "Owner")).select().first()
    return role

# Create a new community from a given payload. Throws an error if no payload is given, or the community already exists.
def create():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'community_name' not in payload or 'community_description' not in payload:
        return dict(msg="Payload missing required fields.")
    if db(db.communities.community_name == payload['community_name']).count() > 0:
        return dict(msg="Community already exists.")
    db.communities.insert(community_name=payload['community_name'], community_description=payload['community_description'])
    return dict(msg="Community created.")

# Create a new community with a payload only containing the community name. Throws an error if no payload is given, or the community already exists.
def create_by_name():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)

    # Check if the community name and identity name fields are in the payload.
    if 'community_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields. Need community_name and identity_name.")
    
    # Check if the 'description' field is in the payload. If not, set it to an empty string.
    if 'description' not in payload:
        payload['description'] = ""

    # Check if the community already exists.
    if db(db.communities.community_name == payload['community_name']).count() > 0:
        return dict(msg="Community already exists.")
    
    # Create the community with the given community name.
    db.communities.insert(community_name=payload['community_name'], community_description=payload['description'])

    # Create the default roles for the community.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    create_roles(community.id)

    # After a community is created, add the identity as a member of the community with the Owner role from the roles table.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    identity = db(db.identities.name == payload['identity_name']).select().first()

    # If the identity does not exist, return an error.
    if not identity:
        return dict(msg="Identity does not exist.")

    # From the roles table, get the Owner role for the community.
    role = get_owner_role(community.id)
    db.community_members.insert(community_id=community.id, identity_id=identity.id, role_id=role.id, currency=0)

    return dict(msg="Community created. You have been granted the Owner role of this community.")

# Get all communities.
def get_all():
    communities = db(db.communities).select()
    return dict(data=communities)

# Get a community by its name. If the community does not exist, return an error.
def get_by_name():
    community_name = request.args(0)
    community_name = decode_name(community_name)
    if not community_name:
        return dict(msg="No community name given.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    return dict(data=community)

# Update a community by its name. If the community does not exist, return an error.
def update_by_name():
    community_name = request.args(0)
    community_name = decode_name(community_name)
    if not community_name:
        return dict(msg="No community name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'community_name' not in payload or 'community_description' not in payload:
        return dict(msg="Payload missing required fields.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    community.update_record(community_name=payload['community_name'], community_description=payload['community_description'])
    return dict(msg="Community updated.")

# Update a community's description by its name. This can only be done by an identity_name that is part of the community with the Owner role. If the community does not exist, return an error.
def update_desc_by_name():
    community_name = request.args(0)
    community_name = decode_name(community_name)
    if not community_name:
        return dict(msg="No community name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'identity_name' not in payload or 'community_description' not in payload:
        return dict(msg="Payload missing required fields.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not member:
        return dict(msg="You are not a member of this community.")
    role = db(db.roles.id == member.role_id).select().first()
    if role.name != "Owner":
        return dict(msg="You do not have permission to update this community's description.")
    community.update_record(community_description=payload['community_description'])
    return dict(msg="Community description updated.")
    

# Delete a community by its name. This can only be done by an identity_name that is part of the community with the Owner role. If the community does not exist, return an error. 
def delete_by_name():
    community_name = request.args(0)
    community_name = decode_name(community_name)
    if not community_name:
        return dict(msg="No community name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'identity_name' not in payload:
        return dict(msg="Payload missing required fields.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not member:
        return dict(msg="You are not a member of this community.")
    role = db(db.roles.id == member.role_id).select().first()
    if role.name != "Owner":
        return dict(msg="You do not have permission to delete this community.")
    db(db.communities.community_name == community_name).delete()
    return dict(msg="Community deleted.")

    
