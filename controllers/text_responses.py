# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from text_response.py")

# Helper function to decode names with space in
def decode_name(name):
    if not name:
        return None
    name = name.replace("%20", " ")
    name = name.replace("_", " ")

    return name

# Helper function to retrieve a community object from a given name
def get_community(name):
    return db(db.communities.community_name == name).select().first()

# Helper function to return a text response object from a given text value and a community id
def get_text_response(text, community_id):    
    return db((db.text_responses.community_id == community_id) & (db.text_responses.text_val == text)).select().first()

# From a given payload, create a new text response using a text value and a response value found in the payload. If the text response already exists, return an error.
# This is stored per community name found in the arguments.
def set_text_response():
    community_name = request.args(0)
    payload = request.body.read()
    
    # Check if the payload is valid
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'text' not in payload or 'response' not in payload:
        return dict(msg="Payload missing required fields.", status=400)
    
    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Check if the text response already exists. If it does, update the response value. Else create a new text response.
    text_response = get_text_response(payload['text'], community.id)
    if text_response:
        text_response.update_record(response_val=payload['response'])
    else:
        insertObj = {
            'community_id': community.id,
            'text_val': payload['text'],
            'response_val': payload['response']
        }
        db.text_responses.insert(**insertObj)

    return dict(msg="Text response set.", status=201)

# This function updates a text response by a given text value. If the text response does not exist, return an error.
def update_text_response():
    community_name = request.args(0)
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'text' not in payload or 'response' not in payload:
        return dict(msg="Payload missing required fields.", status=400)
    
    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    text_response = get_text_response(payload['text'], community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    text_response.update_record(response_val=payload['response'])
    return dict(msg="Text response updated.", status=200)

# Get a list of the text responses for a given community name
def get_all():
    community_name = request.args(0)

    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Get all text responses for the given community
    text_responses = db(db.text_responses.community_id == community.id).select()
    data = [dict(text=text_response.text_val, response=text_response.response_val) for text_response in text_responses]
    
    return dict(status=200, data=data)

# Get a text response by its text value. If the text response does not exist, return an error.
def get_by_text():
    community_name = request.args(0)

    # Check if the payload is valid
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'text' not in payload:
        return dict(msg="Payload missing required fields. Please provide the 'text' field.", status=400)

    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Check if the text response exists
    text_response = get_text_response(payload['text'], community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    return dict(status=200, msg=text_response.response_val)

# Delete a text response by its text value. If the text response does not exist, return an error.
def delete_by_text():
    community_name = request.args(0)

    # Check if the payload is valid
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'text' not in payload:
        return dict(msg="Payload missing required fields. Please provide the 'text' field.", status=400)
    
    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Check if the text response exists
    text_response = get_text_response(payload['text'], community.id)
    if not text_response:
        return dict(msg="Text response not found.", status=404)
    
    text_response.delete_record()
    return dict(msg="Text response deleted.", status=200)