# -*- coding: utf-8 -*-
from json import loads as jloads
from py4web import URL, abort, action, redirect, request

from ..common import (T, auth, authenticated, cache, db, flash, logger, session,
                     unauthenticated)

from ..models import waddle_helpers

# Define the base route for the alias_commands controller
base_route = "api/alias_commands/"

# try something like
def index(): return dict(message="hello from alias_commands.py")

# From a given payload, create a new alias command using an alias value and a command value found in the payload. If the alias command already exists, return an error.
# This is stored per community name found in the arguments.
@action(base_route + "set_alias_command", method=["POST"])
@action.uses(db)
def set_alias_command():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the alias value to that of the first element in the command string list
    alias = command_str_list[0]

    # Set the command value to that of the second element in the command string list
    command = command_str_list[1]

    # Check if the given alias value is the same as a command in the modules table. If it is, return an error.
    if waddle_helpers.command_exists(alias):
        return dict(msg="Alias value cannot be the same as an existing command. Please choose a different alias value.", status=400)

    # Check if the command exists in the modules table
    if not waddle_helpers.command_exists(command):
        return dict(msg="Command does not exist on Waddlebot. Please check the spelling of the command.", status=404)
    
    # Check if the alias command already exists. If it does, update the response value. Else create a new alias command.
    alias_command = waddle_helpers.get_alias_command(alias, community.id)
    if alias_command:
        alias_command.update_record(command_val=command)
    else:
        insertObj = {
            'community_id': community.id,
            'alias_val': alias,
            'command_val': command
        }
        db.alias_commands.insert(**insertObj)

    return dict(msg=f"Alias set for the command {command} as {alias}.", status=201)

# Get a list of the alias commands for a given community name
@action(base_route + "get_all", method=["GET"])
@action.uses(db)
def get_all():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    
    # Get all alias commands for the given community
    alias_commands = db(db.alias_commands.community_id == community.id).select()
    data = [dict(alias_val=alias_command.alias_val, command_val=alias_command.command_val) for alias_command in alias_commands]
    
    return dict(data= data, status=200)

# Get a alias command by its alias value. If the alias command does not exist, return an error.
@action(base_route + "get_by_alias", method="GET")
@action.uses(db)
def get_by_alias():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the alias value to that of the first element in the command string list
    alias = command_str_list[0]
    
    # Check if the alias command exists
    alias_command = waddle_helpers.get_alias_command(alias, community.id)
    if not alias_command:
        return dict(msg="alias command not found.", status=404)
    
    return dict(status=200, msg=alias_command.command_val)

# Delete a alias command by its alias value. If the alias command does not exist, return an error.
@action(base_route + "delete_by_alias", method="DELETE")
@action.uses(db)
def delete_by_alias():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())
    
    community = payload['community']
    command_str_list = payload['command_string']

    # Set the alias value to that of the first element in the command string list
    alias = command_str_list[0]
    
    # Check if the alias command exists
    alias_command = waddle_helpers.get_alias_command(alias, community.id)
    if not alias_command:
        return dict(msg="alias command not found.", status=404)
    
    alias_command.delete_record()
    return dict(msg="alias command deleted.", status=200)