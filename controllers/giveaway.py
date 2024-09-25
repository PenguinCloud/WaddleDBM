# -*- coding: utf-8 -*-
import json
import uuid
import threading
import requests
import time
import logging
import random

from dataclasses import asdict
from WaddleDBM.dataclasses.matterbridge_classes import matterbridgePayload

# Set the logger configuration
logging.basicConfig(level=logging.INFO)

# TODO: Get the below variables from a config file or environment variables
matterbridgePostURL = 'http://localhost:4200/api/message'

# try something like
def index(): return dict(message="hello from giveaway.py")

# Function to get a routing_gateway channel_id from a given routing_gateway_id. If it doesnt exist, return null.
def get_channel_id(routing_gateway_id: int) -> str:
    routing_gateway = db(db.routing_gateways.id == routing_gateway_id).select().first()
    if not routing_gateway:
        return None
    return routing_gateway.channel_id

# Function to get the account as a combination of the protocol and the server name from a given routing_gateway_id. If it doesnt exist, return null.
def get_account(routing_gateway_id: int) -> str:
    routing_gateway = db(db.routing_gateways.id == routing_gateway_id).select().first()
    if not routing_gateway:
        return None
    gateway_server = db(db.gateway_servers.id == routing_gateway.gateway_server).select().first()
    if not gateway_server:
        return None
    return f"{gateway_server.protocol}.{gateway_server.name}"

# Function to create a matterbridge payload for a given community_id by checking all the gateways connected to the community. Returns None if no gateways are connected to the community.
def create_matterbridge_payloads(community_id: int, message: str) -> list[matterbridgePayload]:
    if not community_id:
        raise ValueError("community_id must be provided")
    if not message:
        raise ValueError("message must be provided")

    community = db(db.communities.id == community_id).select().first()
    if not community:
        raise ValueError(f"No community found with id {community_id}")
    
    # In the routing table, get the routing_gateway_ids for the given community id. If the routing_gateway_ids list is empty, return an error.
    routings = db(db.routing.community_id == community.id).select().first()

    if not routings:
        logging.error("No routings found for the current community.")
        return None
    
    # Get the channel_id and account from the routing_gateway_ids
    channel_ids = []
    accounts = []
    if len(routings.routing_gateway_ids) == 0:
        logging.error("No routing gateways found for the current community. Unable to send a message.")
        return None
    
    for routing_gateway_id in routings.routing_gateway_ids:
        channel_id = get_channel_id(routing_gateway_id)
        account = get_account(routing_gateway_id)
        if channel_id and account:
            channel_ids.append(channel_id)
            accounts.append(account)

    # Create a matterbridge payload for each channel_id and account
    payloads = []
    for channel_id, account in zip(channel_ids, accounts):
        message = f"Event {event_name} is starting in 30 minutes."
        payload = matterbridgePayload(username="WaddleDBM", gateway="discord", account=account, text=message)
        payloads.append(payload)

    # Return the payloads
    return payloads

# A function to send a message to Matterbridge with a given matterbridge payload. Returns a success message if the message is sent successfully.
def send_matterbridge_message(payload: matterbridgePayload) -> None:
    # Send the message to Matterbridge
    try:
        requests.post(matterbridgePostURL, json=asdict(payload))
        logging.info(f"Message sent to Matterbridge successfully.")
    except Exception as e:
        logging.error(f"Error sending message to Matterbridge: {e}")

# Function to create a timeout for a giveaway on a new thread. When the timeout is reached, the giveaway is closed and a winner is randomly selected.
# The winner is announced in the chat of every gateway that the community is connected to, via Matterbridge. 
# If no gateways are connected to a community, the winner is not announced.
def create_giveaway_timeout(timeout: int, guid: str, community_id: int) -> None:
    time.sleep(timeout)
    
    # Get the giveaway from the database
    giveaway = db(db.prizes.guid == guid).select().first()

    # If the giveaway does not exist, return an error
    if not giveaway:
        logging.error(f"Giveaway with guid {guid} does not exist.")
        return None
    
    # If the giveaway is already closed, return an error
    status = db(db.prize_statuses.id == giveaway.prize_status).select().first()

    if status.status_name == "Closed":
        logging.error(f"Giveaway with guid {guid} is already closed.")
        return None
    
    # Get all the entries for the giveaway
    entries = db(db.prize_entries.prize_id == giveaway.id).select()

    # Get the gateway payloads for the community
    payloads = create_matterbridge_payloads(community_id, f"Giveaway with guid {guid} is closed. A winner will be announced shortly.")

    # If there are no payloads, return an error
    if not payloads or len(payloads) == 0:
        logging.error(f"No payloads found for the community with id {community_id}. Unable to announce the winner.")
        return None

    # If there are no entries, close the giveaway and send a message to Matterbridge
    if len(entries) == 0:
        # Close the giveaway
        status = db(db.prize_statuses.status_name == "Closed").select().first()
        db(db.prizes.guid == guid).update(prize_status=status.id)

        # Send a message to Matterbridge
        for payload in payloads:
            send_matterbridge_message(payload)
        
        logging.info(f"Giveaway with guid {guid} is closed. No entries found.")
        return None
    
    # Select a random winner from the entries
    winner = random.choice(entries)

    # Get the winner's identity
    winner_identity = db(db.identities.id == winner.identity_id).select().first()

    # Update the giveaway with the winner's identity
    db(db.prizes.guid == guid).update(winner_identity_id=winner_identity.id)

    # Close the giveaway
    status = db(db.prize_statuses.status_name == "Closed").select().first()

    db(db.prizes.guid == guid).update(prize_status=status.id)

    # Send a message to Matterbridge
    for payload in payloads:
        send_matterbridge_message(payload)

    logging.info(f"Giveaway with guid {guid} is closed. Winner is {winner_identity.identity_name}.")
    return None

# Function to add a giveaway to the database, via the prizes table, per community name. Throws an error if no payload is given.
def create() -> dict:
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # The community_name, prize_name and prize_description are required fields
    if 'community_name' not in payload or 'prize_name' not in payload or 'prize_description' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the community exists
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist. Please provide a valid community name.")
    
    # Check if a timeout is provided, if not, set it to 0
    timeout = 0
    if 'timeout' in payload:
        timeout = payload['timeout']

    # Generate a giveaway guid
    guid = str(uuid.uuid4())

    # The default prize status is "Open". Get the status id from the prize_statuses table for the "Open" status.
    status = db(db.prize_statuses.status_name == "Open").select().first()

    # Insert the giveaway into the prizes table
    db.prizes.insert(
        guid=guid,
        community_id=community.id,
        prize_guid=guid,
        prize_name=payload['prize_name'],
        prize_description=payload['prize_description'],
        winner_identity_id=None,
        prize_status=status.id,
        timeout=timeout
    )

    # If a timeout is provided, create a new thread for the timeout
    if timeout > 0:
        thread = threading.Thread(target=create_giveaway_timeout, args=(timeout, guid, community.id))
        thread.start()

    # Return a success message
    return dict(msg=f"Giveaway created under the name {payload['prize_name']}. If you want to enter the giveaway, type !giveaway enter {guid} in the chat.")

# Function to get all giveways for a given community_name in a payload. Throws an error if no community name is given, or the community does not exist.
def get_all_by_community_name() -> dict:
    # Check that the payload is provided
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # Check that the community_name is provided in the payload
    if 'community_name' not in payload:
        return dict(msg="Payload missing required fields. Please provide a community name in the payload.")
    
    # Check if the community exists
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist. Please provide a valid community name.")
    
    # Get all the giveaways for the community
    giveaways = db(db.prizes.community_id == community.id).select()

    # In the return data, return the prize name, guid, winner_identity_name (If a winner exists), prize_status_name and timeout.
    data = []
    for giveaway in giveaways:
        winner_identity_name = None
        if giveaway.winner_identity_id:
            winner_identity = db(db.identities.id == giveaway.winner_identity_id).select().first()
            winner_identity_name = winner_identity.identity_name
        
        status = db(db.prize_statuses.id == giveaway.prize_status).select().first()

        data.append({
            "prize_name": giveaway.prize_name,
            "guid": giveaway.guid,
            "winner_identity_name": winner_identity_name,
            "prize_status_name": status.status_name,
            "timeout": giveaway.timeout
        })
    
    # Return the data
    return dict(data=data)

# Function to enter a giveaway with a given guid and identity_name from a payload. Throws an error if no guid is provided, or the guid does not exist.
# The identity_name is required to enter the giveaway. The identity_name must be a valid identity_name from the identities table, 
# must be in the same community and community context as the giveaway,
# and must not have already entered the giveaway.

def enter() -> dict:
    # Check that the payload is provided
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # Check that the guid and identity_name are provided in the payload
    if 'guid' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields. Please provide a guid and identity_name in the payload.")
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == payload['guid']).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
    # Check if the identity exists
    identity = db(db.identities.identity_name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist. Please provide a valid identity name.")
    
    # Check if the identity is in the same community as the giveaway
    community = db(db.communities.id == giveaway.community_id).select().first()
    if identity.community_id != community.id:
        return dict(msg="Identity is not in the same community as the giveaway.")
    
    # Check if the identity is currently in the community context where the giveaway is being held
    context = db((db.context.identity_id == identity.id) & (db.context.community_id == community.id)).select().first()
    if not context:
        return dict(msg="Identity is not in the community context where the giveaway is being held. Please switch to that community context first.")
    
    # Check if the identity has already entered the giveaway
    entry = db((db.prize_entries.prize_id == giveaway.id) & (db.prize_entries.identity_id == identity.id)).select().first()
    if entry:
        return dict(msg="Identity has already entered the giveaway.")
    
    # Insert the entry into the entries table
    db.prize_entries.insert(
        prize_id=giveaway.id,
        identity_id=identity.id
    )

    # Return a success message
    return dict(msg=f"Identity {identity.identity_name} has entered the giveaway with guid {giveaway.guid}.")

# Function to get all the entries for a given giveaway guid. Throws an error if no guid is provided, or the guid does not exist.
def get_entries() -> dict:
    # Check that the payload is provided
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # Check that the guid is provided in the payload
    if 'guid' not in payload:
        return dict(msg="Payload missing required fields. Please provide a guid in the payload.")
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == payload['guid']).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
    # Get all the entries for the giveaway
    entries = db(db.prize_entries.prize_id == giveaway.id).select()

    # In the return data, return the identity_name of the entries
    data = []
    for entry in entries:
        identity = db(db.identities.id == entry.identity_id).select().first()

        data.append({
            "identity_name": identity.identity_name
        })
    
    # Return the data
    return dict(data=data)

# Function to remove a giveaway with a given guid. Throws an error if no guid is provided, or the guid does not exist.
def remove() -> dict:
    # Check that the payload is provided
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # Check that the guid is provided in the payload
    if 'guid' not in payload:
        return dict(msg="Payload missing required fields. Please provide a guid in the payload.")
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == payload['guid']).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
    # Delete the giveaway from the prizes table
    db(db.prizes.guid == payload['guid']).delete()

    # Return a success message
    return dict(msg=f"Giveaway with guid {payload['guid']} has been removed.")

# A function to close a giveway with a given guid and then setting a winner, according to a winner_identity_name provided in the payload. 
# If no winner_identity_name is provided, a random winner is selected from the entries.
# Throws an error if no guid is provided, or the guid does not exist. Also throws an error if the giveaway is already closed, or the identity_name is not valid.
def close_with_winner() -> dict:
    # Check that the payload is provided
    payload = request.body.read()

    if not payload:
        return dict(msg="No payload given.")
    
    payload = json.loads(payload)

    # Check that the guid is provided in the payload
    if 'guid' not in payload:
        return dict(msg="Payload missing required fields. Please provide a guid in the payload.")
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == payload['guid']).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
    # Check if the giveaway is already closed
    status = db(db.prize_statuses.id == giveaway.prize_status).select().first()

    if status.status_name == "Closed":
        return dict(msg="Giveaway is already closed.")
    
    # If a winner_identity_name is provided, check if the identity exists
    if 'winner_identity_name' in payload:
        identity = db(db.identities.identity_name == payload['winner_identity_name']).select().first()
        if not identity:
            return dict(msg="Identity does not exist. Please provide a valid identity name.")
    
    # Get all the entries for the giveaway
    entries = db(db.prize_entries.prize_id == giveaway.id).select()

    # If there are no payloads, return an error
    if not payloads:
        return dict(msg="No payloads found for the community. Unable to announce the winner.")
    
    # If no winner_identity_name is provided, select a random winner from the entries
    if 'winner_identity_name' not in payload:
        winner = random.choice(entries)
        winner_identity = db(db.identities.id == winner.identity_id).select().first()
    else:
        winner_identity = identity

    # Update the giveaway with the winner's identity
    db(db.prizes.guid == payload['guid']).update(winner_identity_id=winner_identity.id)

    # Close the giveaway
    status = db(db.prize_statuses.status_name == "Closed").select().first()

    db(db.prizes.guid == payload['guid']).update(prize_status=status.id)

    # Get the gateway payloads for the community
    payloads = create_matterbridge_payloads(giveaway.community_id, f"Giveway with guid {payload['guid']} is closed. Winner is {winner_identity.identity_name}.")

    # If there are no payloads, return an error
    if not payloads or len(payloads) == 0:
        return dict(msg="No payloads found for the community. Unable to announce the winner.")
    
    # Send a message to Matterbridge
    for payload in payloads:
        send_matterbridge_message(payload)

    # Return a success message
    return dict(msg=f"Giveaway with guid {payload['guid']} is successfully closed.")

# TODO: Create a function that sends a DM to the winner of the giveaway. The function should take the guid of the giveaway and the message to send as input.