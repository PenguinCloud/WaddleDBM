# -*- coding: utf-8 -*-
from json import loads as jloads

from py4web import URL, abort, action, redirect, request
from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

# Define the base route for the text_responses controller
base_route = "api/text_responses/"

# try something like
def index(): return dict(message="hello from text_response.py")

# From a given payload, create a new text response using a text value and a response value found in the payload. If the text response already exists, return an error.
# This is stored per community name found in the arguments.
@action(base_route + "set_text_response", method="POST")
@action.uses(db)
def set_text_response():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the text variable to the first element in the command str_list
    text = command_str_list[0]

    # Set the response variable to the first element in the command str_list
    response = command_str_list[1]
    
    # Check if the text response already exists. If it does, update the response value. Else create a new text response.
    text_response = waddle_helpers.get_text_response(text, community.id)
    if text_response:
        text_response.update_record(response_val=response)
    else:
        insertObj = {
            'community_id': community.id,
            'text_val': text,
            'response_val': response
        }
        db.text_responses.insert(**insertObj)

    return dict(msg="Text response set.", status=201)

# This function updates a text response by a given text value. If the text response does not exist, return an error.
def update_text_response():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the text variable to the first element in the command str_list
    text = command_str_list[0]

    # Set the response variable to the first element in the command str_list
    response = command_str_list[1]
    
    text_response = waddle_helpers.get_text_response(text, community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    text_response.update_record(response_val=response)
    return dict(msg="Text response updated.", status=200)

# Get a list of the text responses for a given community name
@action(base_route + "get_all", method="GET")
@action.uses(db)
def get_all():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    
    # Get all text responses for the given community
    text_responses = db(db.text_responses.community_id == community.id).select()
    data = [dict(text=text_response.text_val, response=text_response.response_val) for text_response in text_responses]
    
    return dict(status=200, data=data)

# Get a text response by its text value. If the text response does not exist, return an error.
@action(base_route + "get_by_text", method="GET")
@action.uses(db)
def get_by_text():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the text variable to the first element in the command str_list
    text = command_str_list[0]
    
    # Check if the text response exists
    text_response = waddle_helpers.get_text_response(text, community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    return dict(status=200, msg=text_response.response_val)

# Delete a text response by its text value. If the text response does not exist, return an error.
@action(base_route + "delete_by_text", method="DELETE")
@action.uses(db)
def delete_by_text():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the text variable to the first element in the command str_list
    text = command_str_list[0]
    
    # Check if the text response exists
    text_response = waddle_helpers.get_text_response(text, community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    text_response.delete_record()
    return dict(msg="Text response deleted.", status=200)