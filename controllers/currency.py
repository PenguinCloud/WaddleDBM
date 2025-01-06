# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from currency.py")

# Using a community name in the arguments and an identity name in the payload, get the currency of the identity in the community. 
# If the community or identity does not exist, return an error.
def get_currency():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    
    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not a member of the community. Join the community first.")

    currency = db((db.currency.identity_id == identity.id) & (db.currency.community_id == community.id)).select().first()

    # If the currency does not exist, create it.
    if not currency:
        currency = db.currency.insert(identity_id=identity.id, community_id=community.id)

    return dict(msg=f"{payload['identity_name']} has {community_member.currency} currency in the community {community.name}.")

# Using a community name, identity name, and amount, add the amount to the member's currency in the community. If the community or 
# member does not exist, return an error.
def add_currency():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the amount to the first element in the command string list.
    amount = command_str_list[0]
    
    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not a member of the community. Join the community first.")

    currency = db((db.currency.identity_id == identity.id) & (db.currency.community_id == community.id)).select().first()

    # If the currency does not exist, create it.
    if not currency:
        currency = db.currency.insert(identity_id=identity.id, community_id=community.id)
    
    # Add the amount to the member's currency.
    currency.update_record(currency=currency.currency + amount)

    return dict(msg=f"{payload['identity_name']} has {currency.currency} currency in the community {community.name}.")

# Using a community name, identity name, and amount, subtract the amount from the member's currency in the community. If the community or
# member does not exist, return an error.
def subtract_currency():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the amount to the first element in the command string list.
    amount = command_str_list[0]
    
    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not a member of the community. Join the community first.")

    currency = db((db.currency.identity_id == identity.id) & (db.currency.community_id == community.id)).select().first()

    # If the currency does not exist, create it.
    if not currency:
        currency = db.currency.insert(identity_id=identity.id, community_id=community.id)
    
    # Subtract the amount from the member's currency.
    currency.update_record(currency=currency.currency - amount)

    return dict(msg=f"{payload['identity_name']} has {currency.currency} currency in the community {community.name}.")

# Using a community name, identity name, and amount, set the member's currency in the community to the amount. If the community or
# member does not exist, return an error.
def set_currency():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the amount to the first element in the command string list.
    amount = command_str_list[0]
    
    # Check if the member is a member of the community.
    community_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == identity.id)).select().first()
    if not community_member:
        return dict(msg="Identity is not a member of the community. Join the community first.")

    currency = db((db.currency.identity_id == identity.id) & (db.currency.community_id == community.id)).select().first()

    # If the currency does not exist, create it.
    if not currency:
        currency = db.currency.insert(identity_id=identity.id, community_id=community.id)

    # Set the member's currency to the amount.
    currency.update_record(currency=amount)

    return dict(msg=f"{payload['identity_name']} has {currency.currency} currency in the community {community.name}.")

# Using a community name, a sender member name, a receiver member name, and an amount, transfer the amount from the sender to the receiver. 
# If the community, sender, or receiver does not exist, return an error. If the sender does not have enough currency, return an error.
def transfer_currency():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    if not payload:
        return dict(msg="This script could not execute. Please ensure that the identity_name, community_name and command_string is provided.", error=True, status=400)
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the receiver name to the first element and the amount to the second element in the command string list.
    receiver_name = command_str_list[0]
    amount = command_str_list[1]
    
    # Check if the sender exists.
    sender = db((db.identities.name == identity.name)).select().first()
    if not sender:
        return dict(msg="Sender does not exist.")
    
    # Check if the receiver exists.
    receiver = db((db.identities.name == receiver_name)).select().first()
    if not receiver:
        return dict(msg="Receiver does not exist.")
    
    # Check if the sender is a member of the community.
    sender_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == sender.id)).select().first()
    if not sender_member:
        return dict(msg="Sender is not a member of the community. Join the community first.")
    
    # Check if the receiver is a member of the community.
    receiver_member = db((db.community_members.community_id == community.id) & (db.community_members.identity_id == receiver.id)).select().first()
    if not receiver_member:
        return dict(msg="Receiver is not a member of the community. Join the community first.")

    sender_currency = db((db.currency.identity_id == sender.id) & (db.currency.community_id == community.id)).select().first()
    receiver_currency = db((db.currency.identity_id == receiver.id) & (db.currency.community_id == community.id)).select().first()

    # If the sender's currency does not exist, create it.
    if not sender_currency:
        sender_currency = db.currency.insert(identity_id=sender.id, community_id=community.id)
    
    # If the receiver's currency does not exist, create it.
    if not receiver_currency:
        receiver_currency = db.currency.insert(identity_id=receiver.id, community_id=community.id)

    # If the sender does not have enough currency, return an error.
    if sender_currency.currency < amount:
        return dict(msg="Sender does not have enough currency.")
    
    # Subtract the amount from the sender's currency.
    sender_currency.update_record(currency=sender_currency.currency - amount)

    # Add the amount to the receiver's currency.
    receiver_currency.update_record(currency=receiver_currency.currency + amount)

    return dict(msg=f"{sender.name} has {sender_currency.currency} currency and {receiver_name} has {receiver_currency.currency} currency in the community {community.name}.")
