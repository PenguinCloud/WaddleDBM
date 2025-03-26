# -*- coding: utf-8 -*-
import json
import uuid
import threading
import requests
import time
import logging
import random
import os

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers, mat_helpers

from ..modules.auth_utils import basic_auth

# Define the base route for the giveaway controller
base_route = "api/giveaway/"

# Set the logger configuration
logging.basicConfig(level=logging.INFO)



# try something like
def index(): return dict(message="hello from giveaway.py")

# A helper function to close a giveaway with a given guid.
def close_giveaway(guid: str) -> None:
    logging.warning(f"Closing giveaway with guid {guid}")
    # Get the status id for the "Closed" status from the prize_statuses table
    status = db(db.prize_statuses.status_name == "Closed").select().first()

    # Check if the giveaway exists\
    giveaway = db(db.prizes.guid == guid).select().first()
    if not giveaway:
        logging.error(f"Giveaway with guid {guid} does not exist.")
        return None
    
    # Update the giveaway with the "Closed" status
    db(db.prizes.guid == guid).update(prize_status=status.id)


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
    payloads = mat_helpers.create_matterbridge_payloads(community_id, f"Giveaway with guid {guid} is closed. A winner will be announced shortly.")

    # If there are no payloads, return an error
    if not payloads or len(payloads) == 0:
        logging.error(f"No payloads found for the community with id {community_id}. Unable to announce the winner.")
        return None

    # If there are no entries, close the giveaway and send a message to Matterbridge
    if len(entries) == 0:
        # Close the giveaway
        close_giveaway(guid)

        # Send a message to Matterbridge
        for payload in payloads:
            mat_helpers.send_matterbridge_message(payload)
        
        logging.warning(f"Giveaway with guid {guid} is closed. No entries found.")
        return None
    
    # Select a random winner from the entries
    winner = random.choice(entries)

    # Get the winner's identity
    winner_identity = db(db.identities.id == winner.identity_id).select().first()

    # Update the giveaway with the winner's identity
    db(db.prizes.guid == guid).update(winner_identity_id=winner_identity.id)

    # Close the giveaway
    close_giveaway(guid)

    # Send a message to Matterbridge
    for payload in payloads:
        mat_helpers.send_matterbridge_message(payload)

    logging.warning(f"Giveaway with guid {guid} is closed. Winner is {winner_identity.identity_name}.")
    return None

# A function to close a giveway with a given guid and then setting a winner, according to a winner_identity_name provided in the payload. 
# If no winner_identity_name is provided, a random winner is selected from the entries.
# Throws an error if no guid is provided, or the guid does not exist. Also throws an error if the giveaway is already closed, or the identity_name is not valid.
def validate_giveaway(guid):
    giveaway = db(db.prizes.guid == guid).select().first()
    if not giveaway:
        raise ValueError("Giveaway does not exist.")
    status = db(db.prize_statuses.id == giveaway.prize_status).select().first()
    if status.status_name == "Closed":
        raise ValueError("Giveaway is already closed.")
    return giveaway

# A function to get a winner for a given giveaway. If a winner_identity_name is provided, the winner is set to that identity.
def get_winner(giveaway, winner_identity_name=None):
    if winner_identity_name:
        winner = db(db.identities.identity_name == winner_identity_name).select().first()
        if not winner:
            raise ValueError("Identity does not exist.")
    else:
        entries = db(db.prize_entries.prize_id == giveaway.id).select()
        winner = random.choice(entries)
        winner = db(db.identities.id == winner.identity_id).select().first()
    return winner

# A function to close a giveaway with a given guid and set a winner. If no winner_identity_name is provided, a random winner is selected from the entries.
def close_giveaway_with_winner(giveaway, winner):
    db(db.prizes.guid == giveaway.guid).update(winner_identity_id=winner.id)
    status = db(db.prize_statuses.status_name == "Closed").select().first()
    db(db.prizes.guid == giveaway.guid).update(prize_status=status.id)

# A function to announce the winner of a giveaway in the chat of every gateway that the community is connected to, via Matterbridge.
def announce_winner(giveaway, winner):
    payloads = mat_helpers.create_matterbridge_payloads(giveaway.community_id, f"Giveaway with guid {giveaway.guid} is closed. Winner is {winner.identity_name}.")
    for payload in payloads:
        mat_helpers.send_matterbridge_message(payload)

# Function to add a giveaway to the database, via the prizes table, per community name. Throws an error if no payload is given.
@action(base_route + "create", method="POST")
@action.uses(db)
@basic_auth(auth)
def create() :
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the prize_name and prize_description to the first and second elements in the command string list.
    prize_name = command_str_list[0]
    prize_description = command_str_list[1]
    
    # Check if a timeout is provided, if not, set it to 0
    timeout = payload["timeout"] if "timeout" in payload else 0
    # if 'timeout' in payload:
    #     timeout = payload['timeout']

    # Generate a giveaway guid
    guid = str(uuid.uuid4())

    # The default prize status is "Open". Get the status id from the prize_statuses table for the "Open" status.
    status = db(db.prize_statuses.status_name == "open").select().first()

    # Insert the giveaway into the prizes table
    db.prizes.insert(
        guid=guid,
        community_id=community.id,
        prize_guid=guid,
        prize_name=prize_name,
        prize_description=prize_description,
        winner_identity_id=None,
        prize_status=status.id,
        timeout=timeout
    )

    # If a timeout is provided, create a new thread for the timeout
    if timeout > 0:
        thread = threading.Thread(target=create_giveaway_timeout, args=(timeout, guid, community.id))
        thread.start()

    # Return a success message
    return dict(msg=f"Giveaway created under the name {prize_name}. If you want to enter the giveaway, type !giveaway enter {guid} in the chat.")

# Function to get all giveways for a given community_name in a payload. Throws an error if no community name is given, or the community does not exist.
# Returns the prize name, guid, winner_identity_name (If a winner exists), prize_status_name and timeout.
@action(base_route + "get_all_by_community_name", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_all_by_community_name() :
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    
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
@action(base_route + "enter", method="POST")
@action.uses(db)
@basic_auth(auth)
def enter() :
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the guid to the first element in the command string list.
    guid = command_str_list[0]
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == guid).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
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
@action(base_route + "get_entries", method="GET")
@action.uses(db)
@basic_auth(auth)
def get_entries() :
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the guid to the first element in the command string list.
    guid = command_str_list[0]
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == guid).select().first()
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
def remove() :
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    identity = payload['identity']
    command_str_list = payload['command_string']

    # Set the guid to the first element in the command string list.
    guid = command_str_list[0]
    
    # Check if the giveaway exists
    giveaway = db(db.prizes.guid == guid).select().first()
    if not giveaway:
        return dict(msg="Giveaway does not exist. Please provide a valid guid.")
    
    # Delete the giveaway from the prizes table
    db(db.prizes.guid == guid).delete()

    # Return a success message
    return dict(msg=f"Giveaway with guid {guid} has been removed.")

# Function to close a giveaway with a given guid and set a winner. If no winner_identity_name is provided, a random winner is selected from the entries.
@action(base_route + "close", method="PUT")
@action.uses(db)
@basic_auth(auth)
def close_with_winner():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    command_str_list = payload['command_string']

    # Set the guid to the first element in the command string list.
    guid = command_str_list[0]
    
    if not guid:
        return dict(msg="Please provide a guid in the payload.")

    try:
        giveaway = validate_giveaway(guid)
        winner = get_winner(giveaway, payload.get('winner_identity_name'))
        close_giveaway_with_winner(giveaway, winner)
        announce_winner(giveaway, winner)
        return dict(msg=f"Giveaway with guid {guid} is successfully closed.")
    except ValueError as e:
        return dict(msg=str(e))

# TODO: Create a function that sends a DM to the winner of the giveaway. The function should take the guid of the giveaway and the message to send as input.