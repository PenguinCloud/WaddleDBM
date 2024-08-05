# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from communities.py")

# Create a new community member from a given payload. Throws an error if no payload is given, or the community member id already exists in a given community id
def create_member():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'community_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Missing the required fields. Need community_name and identity_name.")
    
    # Set the default role_id to that of a Member in the roles table.
    role = db(db.roles.name == "Member").select().first()

    # If the Member role does not exist, set the id to 1.
    role_id = 1
    if role:
        role_id = role.id
    
    # If the payload contains a role_id, set the role_id to that value.
    if 'role_id' in payload:
        role_id = payload['role_id']

    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the identity_id from the identities table, using the identity_name, if it exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")

    # Check if the community member already exists in the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if community_member:
        return dict(msg="Community member already exists.")

    # Create the community member.
    db.community_members.insert(community_id=community.id, identity_id=identity.id, role_id=role_id)

    return dict(msg=f"{payload['identity_name']} has joined the community {payload['community_name']}.")

# Get all community members accross all communities.
def get_all():
    community_members = db(db.community_members).select()
    return dict(data=community_members)

# Get all community member names and their roles in a given community id.
def get_names_by_community_id():
    community_id = request.args(0)
    if not community_id:
        return dict(msg="No community id given.")
    community_members = db(db.community_members.community_id == community_id).select()
    community_members = [{"name": member.identity_id.name, "role": member.role_id} for member in community_members]
    return dict(data=community_members)

# Get all community members in a given community id.
def get_by_community_id():
    community_id = request.args(0)
    if not community_id:
        return dict(msg="No community id given.")
    community_members = db(db.community_members.community_id == community_id).select()
    return dict(data=community_members)

# Get community members by a given community name. Return the member names, as well as their roles. If the community does not exist, return an error.
def get_names_by_community_name():
    community_name = request.args(0)
    if not community_name:
        return dict(msg="No community name given.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    community_members = db(db.community_members.community_id == community.id).select()
    community_members = [{"name": member.identity_id.name, "role": member.role_id.name} for member in community_members]
    return dict(data=community_members)

# Update a community member by its community id and member id. If the community member does not exist, return an error.
def update_by_community_id_and_identity_id():
    community_id = request.args(0)
    identity_id = request.args(1)
    if not community_id or not identity_id:
        return dict(msg="No community id or member id given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = json.loads(payload)
    if 'community_id' not in payload or 'identity_id' not in payload or 'role_id' not in payload:
        return dict(msg="Payload missing required fields.")
    community_member = db((db.community_members.community_id == community_id) & (db.community_members.identity_id == identity_id)).select().first()
    if not community_member:
        return dict(msg="Community member does not exist.")
    community_member.update_record(**payload)
    return dict(msg="Community member updated.")

# Delete a community member by its community id and member id. If the community member does not exist, return an error.
def delete_by_community_id_and_identity_id():
    community_id = request.args(0)
    identity_id = request.args(1)
    if not community_id or not identity_id:
        return dict(msg="No community id or member id given.")
    community_member = db((db.community_members.community_id == community_id) & (db.community_members.identity_id == identity_id)).select().first()
    if not community_member:
        return dict(msg="Community member does not exist.")
    community_member.delete_record()
    return dict(msg="Community member deleted.")

# Using the community name and identity name, remove a member from a community.
def remove_member():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name between [] characters.")
    payload = json.loads(payload)
    if 'community_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Missing the required fields. Need community_name between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the identity_id from the identities table, using the identity_name, if it exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
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
    msg = f"{payload['identity_name']} has left the community {payload['community_name']}."
    community_members = db(db.community_members.community_id == community.id).select()
    if len(community_members) > 0:
        owner_role = db(db.roles.name == "Owner").select().first()
        if owner_role:
            community_members[0].update_record(role_id=owner_role.id)
            msg += f" The Owner role has been given to {community_members[0].identity_id.name}."

    return dict(msg=f"{payload['identity_name']} has left the community {payload['community_name']}.")

# Using a community name, identity name, member name and role name, update the role of a member in a community to the given role, if the member exists, the role exists, the community exists, the identity exists, and the identity is the owner of the community.
def update_member_role():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name, identity_name, member_name, and role_name between [] characters.")
    payload = json.loads(payload)
    if 'community_name' not in payload or 'identity_name' not in payload or 'member_name' not in payload or 'role_name' not in payload:
        return dict(msg="Missing the required fields. Need community_name, identity_name, member_name, and role_name between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the identity_id from the identities table, using the identity_name, if it exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")

    # Get the member_id from the identities table, using the member_name, if it exists.
    member = db(db.identities.name == payload['member_name']).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Get the role_id from the roles table, using the role_name, if it exists.
    role = db(db.roles.name == payload['role_name']).select().first()
    if not role:
        return dict(msg="Role does not exist.")
    
    # Get the Owner role from the roles table.
    owner_role = db(db.roles.name == "Owner").select().first()
    if not owner_role:
        return dict(msg="Owner role does not exist.")

    # Check if the identity is the owner of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg=f"{payload['identity_name']} is not a member of the community.")
    if community_member.role_id != owner_role.id:
        return dict(msg=f"{payload['identity_name']} is not the owner of the community.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    # Update the role of the member.
    community_member.update_record(role_id=role.id)

    return dict(msg=f"{payload['member_name']}'s role has been updated to {payload['role_name']}.")

#################################
## Currency Management Section ##
#################################

# Using a community name and a member name, get the currency of the member in the community. If the community or member does not exist, return an error.
def get_currency():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name and identity_name between [] characters.")
    payload = json.loads(payload)
    if 'identity_name' not in payload:
        return dict(msg="Missing the required fields. Need community_name and identity_name between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the member_id from the identities table, using the identity_name, if it exists.
    member = db(db.identities.name == payload['identity_name']).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    return dict(msg=f"{payload['identity_name']} has {community_member.currency} currency in the community {community_name}.")

# Using a community name, member name, and amount, add the amount to the member's currency in the community. If the community or member does not exist, return an error.
def add_currency():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name, identity_name, and amount between [] characters.")
    payload = json.loads(payload)
    if 'identity_name' not in payload or 'amount' not in payload:
        return dict(msg="Missing the required fields. Need community_name, identity_name, and amount between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the member_id from the identities table, using the identity_name, if it exists.
    member = db(db.identities.name == payload['identity_name']).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    # Try to convert the amount to an integer. If it fails, return an error.
    try:
        payload['amount'] = int(payload['amount'])
    except:
        return dict(msg="Amount must be an integer.")

    # Add the amount to the member's currency.
    community_member.update_record(currency=community_member.currency + payload['amount'])

    return dict(msg=f"{payload['identity_name']} has received {payload['amount']} currency.")

# Using a community name, member name, and amount, subtract the amount from the member's currency in the community. If the community or member does not exist, return an error.
def subtract_currency():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name, identity_name, and amount between [] characters.")
    payload = json.loads(payload)
    if 'identity_name' not in payload or 'amount' not in payload:
        return dict(msg="Missing the required fields. Need community_name, identity_name, and amount between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the member_id from the identities table, using the identity_name, if it exists.
    member = db(db.identities.name == payload['identity_name']).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    # Try to convert the amount to an integer. If it fails, return an error.
    try:
        payload['amount'] = int(payload['amount'])
    except:
        return dict(msg="Amount must be an integer.")

    # Subtract the amount from the member's currency.
    community_member.update_record(currency=community_member.currency - payload['amount'])

    return dict(msg=f"{payload['identity_name']} has lost {payload['amount']} currency.")

# Using a community name, member name, and amount, set the member's currency in the community to the amount. If the community or member does not exist, return an error.
def set_currency():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name, identity_name, and amount between [] characters.")
    payload = json.loads(payload)
    if 'identity_name' not in payload or 'amount' not in payload:
        return dict(msg="Missing the required fields. Need community_name, identity_name, and amount between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the member_id from the identities table, using the identity_name, if it exists.
    member = db(db.identities.name == payload['identity_name']).select().first()
    if not member:
        return dict(msg="Member does not exist.")

    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == member.id)).select().first()
    if not community_member:
        return dict(msg="Member is not a member of the community.")

    # Try to convert the amount to an integer. If it fails, return an error.
    try:
        payload['amount'] = int(payload['amount'])
    except:
        return dict(msg="Amount must be an integer.")

    # Set the member's currency to the amount.
    community_member.update_record(currency=payload['amount'])

    return dict(msg=f"{payload['identity_name']}'s currency has been set to {payload['amount']}.")

# Using a community name, a sender member name, a receiver member name, and an amount, transfer the amount from the sender to the receiver. 
# If the community, sender, or receiver does not exist, return an error. If the sender does not have enough currency, return an error.
def transfer_currency():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given. Please provide a community_name, identity_name, receiver_name, and amount between [] characters.")
    payload = json.loads(payload)
    if 'identity_name' not in payload or 'receiver_name' not in payload or 'amount' not in payload:
        return dict(msg="Missing the required fields. Need community_name, identity_name, receiver_name, and amount between [] characters.")
    
    # Get the community_id from the communities table, using the community_name, if it exists.
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Get the sender_id from the identities table, using the identity_name, if it exists.
    sender = db(db.identities.name == payload['identity_name']).select().first()
    if not sender:
        return dict(msg="Sender does not exist.")

    # Get the receiver_id from the identities table, using the receiver_name, if it exists.
    receiver = db(db.identities.name == payload['receiver_name']).select().first()
    if not receiver:
        return dict(msg="Receiver does not exist.")

    # Check if the sender is a member of the community.
    sender_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == sender.id)).select().first()
    if not sender_member:
        return dict(msg="Sender is not a member of the community.")

    # Check if the receiver is a member of the community.
    receiver_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == receiver.id)).select().first()
    if not receiver_member:
        return dict(msg="Receiver is not a member of the community.")

    # Try to convert the amount to an integer. If it fails, return an error.
    try:
        payload['amount'] = int(payload['amount'])
    except:
        return dict(msg="Amount must be an integer.")

    # Check if the sender has enough currency to transfer.
    if sender_member.currency < payload['amount']:
        return dict(msg="Sender does not have enough currency to transfer.")

    # Transfer the amount from the sender to the receiver.
    sender_member.update_record(currency=sender_member.currency - payload['amount'])
    receiver_member.update_record(currency=receiver_member.currency + payload['amount'])

    return dict(msg=f"{payload['identity_name']} has transferred {payload['amount']} currency to {payload['receiver_name']}.")