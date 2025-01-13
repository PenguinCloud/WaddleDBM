# -*- coding: utf-8 -*-
from json import loads as jloads
from json import dumps as jdumps
from datetime import datetime, timedelta
from threading import Thread
import requests
import time
import logging

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

# Define the base route for the calendar controller
base_route = "api/calendar/"

# TODO: Get the below variables from a config file
matterbridgePostURL = 'http://localhost:4200/api/message'

stop_threads = False

# try something like
def index(): return dict(message="hello from calendar.py")

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

# Create a new calender event from a given payload. Throws an error if no payload is given.
@action("create", method="POST")
@action.uses(db)
def create():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the event name to that of the first element in the command string list
    event_name = command_str_list[0]

    # Set the event description to that of the second element in the command string list
    event_description = command_str_list[1]

    # Set the event start to that of the third element in the command string list
    event_start = command_str_list[2]

    # Set the event end to that of the fourth element in the command string list
    event_end = command_str_list[3]
    
    # Create the event
    db.calendar.insert(community_id=community.id, event_name=event_name, event_description=event_description, event_start=event_start, event_end=event_end, notification_sent=False)
    return dict(msg="Event created.", status=201)

# Get all calender events.
def get_all():
    events = db(db.calendar).select()
    return dict(data=events, status=200)

# Get a calender event by its name. If the event does not exist, return an error.
def get_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    command_str_list = payload['command_string']

    # Set the event name to that of the first element in the command string list
    event_name = command_str_list[0]

    event = db(db.calendar.event_name == event_name).select().first()
    if not event:
        return dict(msg="Event not found.", status=404)
    return dict(data=event, status=200)

# Get calendar events by a community name and between a start and end date from a payload. Return an error if the community does not exist.
@action("get_by_community", method="GET")
@action.uses(db)
def get_by_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']
    
    # The start and end date are optional. The start date is the current date and the end date is the current date plus 30 days.
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    # If the start and end date are provided, set them to the given values.
    if len(command_str_list) > 0:
        start_date = command_str_list[0]
        end_date = command_str_list[1]

    events = db((db.calendar.community_id == community.id) & (db.calendar.event_start >= start_date) & (db.calendar.event_start <= end_date)).select()
    return dict(data=events, status=200)

# Update a calendar event by its event name and community name. If the event does not exist, return an error.
@action("update_by_name", method="PUT")
@action.uses(db)
def update_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the event name to that of the first element in the command string list
    event_name = command_str_list[0]

    event = db(db.calendar.event_name == event_name).select().first()

    if not event:
        return dict(msg="Event not found.", status=404)
    
    # Set the event description to that of the second element in the command string list
    event_description = command_str_list[1]

    # Set the event start to that of the third element in the command string list
    event_start = command_str_list[2]

    # set the event end to that of the fourth element in the command string list
    event_end = command_str_list[3]

    # Set the community id to that of the community
    event.community_id = community.id
    
    # Update the event
    if event_description:
        event.event_description = event_description
    if event_start:
        event.event_start = event_start
    if event_end:
        event.event_end = event_end
    
    event.update_record()
    return dict(msg="Event updated.", status=200)

# Delete a calendar event by its name and community name in a payload. If the event does not exist, return an error.
@action("delete_by_name", method="DELETE")
@action.uses(db)
def delete_by_name():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the event name to that of the first element in the command string list
    event_name = command_str_list[0]

    event = db(db.calendar.event_name == event_name).select().first()
    if not event:
        return dict(msg="Event not found.", status=404)

    if event.community_id == community.id:
        event.delete_record()
        return dict(msg="Event deleted.", status=200)
    else:
        return dict(msg="Event not found.", status=404)
    
# A loop function to check if an event is starting in 30 minutes. If it is, send a message to the Matterbridge.
def check_events_start():
    logging.warning("Starting calendar event check loop.")
    while True:
        logging.warning("Checking for events.")
        events = db(db.calendar).select()
        if events:
            logging.warning("Events found. Checking if any events are starting in 30 minutes.")
            for event in events:
                if (event.event_start - timedelta(minutes=30) <= datetime.now() <= event.event_start) and event.not_start_sent == False:
                    event_name = event.event_name

                    # Using the event's community id, get the community name
                    community = db(db.communities.id == event.community_id).select().first()
                    if not community:
                        logging.error("Community not found. The given community must have been deleted.")
                        continue
                    
                    # In the routing table, get the routing_gateway_ids for the given community id. If the routing_gateway_ids list is empty, return an error.
                    routings = db(db.routing.community_id == community.id).select().first()

                    if not routings:
                        logging.error("No routings found for the current community.")
                        continue
                    
                    # Get the channel_id and account from the routing_gateway_ids
                    channel_ids = []
                    accounts = []
                    if len(routings.routing_gateway_ids) == 0:
                        logging.error("No routing gateways found for the current community. Unable to send a message.")
                        continue
                    
                    for routing_gateway_id in routings.routing_gateway_ids:
                        channel_id = get_channel_id(routing_gateway_id)
                        account = get_account(routing_gateway_id)
                        if channel_id and account:
                            channel_ids.append(channel_id)
                            accounts.append(account)

                    # Send a message to the Matterbridge for each channel_id and account
                    for channel_id, account in zip(channel_ids, accounts):
                        try:
                            message = f"Event {event_name} is starting in 30 minutes."
                            payload = {
                                "username": "Waddle Bot",
                                "gateway": channel_id,
                                "account": account,
                                "text": message
                            }
                            requests.post(matterbridgePostURL, data=jdumps(payload), headers={'Content-Type': 'application/json'})
                        except Exception as e:
                            logging.error(f"Error sending message to Matterbridge: {e}")
                    
                    logging.warning(f"Event {event_name} is starting in 30 minutes. Messages sent to the Matterbridge.")

                    # Update the notification sent field in the event record
                    event.update_record(not_start_sent=True)

                    db.commit()

            if stop_threads:
                break
        # Sleep for 1 minute
        time.sleep(60)

# A loop function to check if an event has ended. If it has, send a message to the Matterbridge.
def check_events_end():
    logging.warning("Starting calendar event check loop.")
    while True:
        logging.warning("Checking for events.")
        events = db(db.calendar).select()
        if events:
            logging.warning("Events found. Checking if any events are ending.")
            for event in events:
                if event.event_end >= datetime.now() and event.not_end_sent == False:
                    event_name = event.event_name

                    # Using the event's community id, get the community name
                    community = db(db.communities.id == event.community_id).select().first()
                    if not community:
                        logging.error("Community not found. The given community must have been deleted.")
                        continue
                    
                    # In the routing table, get the routing_gateway_ids for the given community id. If the routing_gateway_ids list is empty, return an error.
                    routings = db(db.routing.community_id == community.id).select().first()

                    if not routings:
                        logging.error("No routings found for the current community.")
                        continue
                    
                    # Get the channel_id and account from the routing_gateway_ids
                    channel_ids = []
                    accounts = []
                    if len(routings.routing_gateway_ids) == 0:
                        logging.error("No routing gateways found for the current community. Unable to send a message.")
                        continue
                    
                    for routing_gateway_id in routings.routing_gateway_ids:
                        channel_id = get_channel_id(routing_gateway_id)
                        account = get_account(routing_gateway_id)
                        if channel_id and account:
                            channel_ids.append(channel_id)
                            accounts.append(account)

                    # Send a message to the Matterbridge for each channel_id and account
                    for channel_id, account in zip(channel_ids, accounts):
                        try:
                            message = f"Event {event_name} is ending."
                            payload = {
                                "username": "Waddle Bot",
                                "gateway": channel_id,
                                "account": account,
                                "text": message
                            }
                            requests.post(matterbridgePostURL, data=jdumps(payload), headers={'Content-Type': 'application/json'})
                        except Exception as e:
                            logging.error(f"Error sending message to Matterbridge: {e}")
                    
                    logging.warning(f"Event {event_name} is ending. Messages sent to the Matterbridge.")

                    # Update the notification sent field in the event record
                    event.update_record(not_end_sent=True)

                    db.commit()

            if stop_threads:
                break

        # Sleep for 1 minute
        time.sleep(60)

# Function to start the check_events loop in a new thread.
def start_event_check():
    event_start_check_thread = Thread(target=check_events_start)
    event_start_check_thread.start()

    event_end_check_thread = Thread(target=check_events_end)
    event_end_check_thread.start()

    return dict(msg="Event check loop started.")
