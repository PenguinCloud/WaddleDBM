# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from alias_commands.py")

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

# Helper function to return a alias command object from a given alias value and a community id
def get_alias_command(alias, community_id):    
    return db((db.alias_commands.community_id == community_id) & (db.alias_commands.alias_val == alias)).select().first()

# Helper function to raplace all spaces in given command string with _ and return the new string
def replace_spaces(command):
    return command.replace(" ", "_")

# Helper function to check if a given command exists in the marketplace_modules table
def command_exists(command):
    command = replace_spaces(command)
    return db(db.marketplace_modules.metadata.like(f'%"{command}"%')).select().first()

# From a given payload, create a new alias command using an alias value and a command value found in the payload. If the alias command already exists, return an error.
# This is stored per community name found in the arguments.
def set_alias_command():
    community_name = request.args(0)
    payload = request.body.read()
    
    # Check if the payload is valid
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'alias' not in payload or 'command' not in payload:
        return dict(msg="Payload missing required fields.", status=400)
    
    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)

    # Check if the given alias value is the same as a command in the marketplace_modules table. If it is, return an error.
    if command_exists(payload['alias']):
        return dict(msg="Alias value cannot be the same as an existing command. Please choose a different alias value.", status=400)

    # Check if the command exists in the marketplace_modules table
    if not command_exists(payload['command']):
        return dict(msg="Command does not exist on Waddlebot. Please check the spelling of the command.", status=404)
    
    # Check if the alias command already exists. If it does, update the response value. Else create a new alias command.
    alias_command = get_alias_command(payload['alias'], community.id)
    if alias_command:
        alias_command.update_record(command_val=payload['command'])
    else:
        insertObj = {
            'community_id': community.id,
            'alias_val': payload['alias'],
            'command_val': payload['command']
        }
        db.alias_commands.insert(**insertObj)

    return dict(msg=f"Alias set for the command {payload['command']} as {payload['alias']}.", status=201)

# Get a list of the alias commands for a given community name
def get_all():
    community_name = request.args(0)

    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Get all alias commands for the given community
    alias_commands = db(db.alias_commands.community_id == community.id).select()
    data = []
    for alias_command in alias_commands:
        data.append(dict(
            alias_val=alias_command.alias_val,
            command_val=alias_command.command_val
        ))
    
    return dict(status=200, data=data)

# Get a alias command by its alias value. If the alias command does not exist, return an error.
def get_by_alias():
    community_name = request.args(0)

    # Check if the payload is valid
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'alias' not in payload:
        return dict(msg="Payload missing required fields. Please provide the 'alias' field.", status=400)

    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Check if the alias command exists
    alias_command = get_alias_command(payload['alias'], community.id)
    if not alias_command:
        return dict(msg="alias command not found.", status=404)
    
    return dict(status=200, msg=alias_command.command_val)

# Delete a alias command by its alias value. If the alias command does not exist, return an error.
def delete_by_alias():
    community_name = request.args(0)

    # Check if the payload is valid
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.", status=400)
    
    payload = json.loads(payload)
    if 'alias' not in payload:
        return dict(msg="Payload missing required fields. Please provide the 'alias' field.", status=400)
    
    # Check if the community exists in the communities table
    community = get_community(community_name)
    if not community:
        return dict(msg="Community does not exist.", status=404)
    
    # Check if the alias command exists
    alias_command = get_alias_command(payload['alias'], community.id)
    if not alias_command:
        return dict(msg="alias command not found.", status=404)
    
    alias_command.delete_record()
    return dict(msg="alias command deleted.", status=200)