# -*- coding: utf-8 -*-
import json
import logging

from py4web import URL, abort, action, redirect, request, response
from py4web.utils.form import Form, FormStyleBulma
from ..common import (T, db, session, Field)
from pydal.validators import IS_NOT_EMPTY

# Define the base route for the module onboarding controller
base_route = "api/module_onboarding/"

# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)

# try something like
def index(): return dict(message="hello from module onboarding.py")

# A helper function to return the module_type_id of a module type with the
# given name of "Community"
def get_community_module_type_id():
    module_type = db(db.module_types.name == "Community").select().first()
    if not module_type:
        return 1
    return module_type.id

# Helper function to insert a command in the module_commands table. Returns a flag to indicate
# if the command exists in the database or not.
def insert_command(module_id, command):
    logging.warning("Inserting command into the database...")
    flag = False
    # Check if the command object is not empty and if it already exists in the database
    if command and not db((db.module_commands.command_name == command['command_name'])).select().first():
        # Insert the command object into the database
        db.module_commands.insert(module_id=module_id, **command)
        # Print a response flash
        response.flash = 'New command has been added to your module.'
    else:
        logging.warning("Command already exists in the database. Skipping...")
        # Print a response flash
        response.flash = 'This command already exists. Please check the command name.'
        flag = True

    return flag

# Helper function to retrieve a list of commands from the module_commands table
def get_commands(module_id):
    logging.warning("Getting commands from the database...")
    return db(db.module_commands.module_id == module_id).select()

# Helper function to check if a given command name already exists in the given metadata object as a key
def command_exists_in_metadata(command_name, metadata):
    logging.warning("Checking if command exists in metadata...")
    return command_name in metadata

# Helper function to check if the command object contains all the required fields
def command_object_is_valid(command):
    logging.warning("Checking if command object is valid...")
    return 'command_name' in command and 'action_url' in command and 'request_method' in command and 'request_parameters' in command and 'payload_keys' in command and 'req_priv_list' in command and 'description' in command

# Helper function to convert a given command string into a command string 
# that can be used as a key in the metadata object, but replacing spaces 
# with underscores and adding a # at the start.
def convert_command_to_key(command):
    # Check if the first character starts with a # or !. If not, add a #
    if command[0] != "#" and command[0] != "!":
        command = "#" + command
    return command.replace(" ", "_")

# Helper function to convert a given command key back into a command string
def normalize_value(value):
    if value is None:
        return []
    elif isinstance(value, str):
        return [value]
    return value

# Helper function to convert the instances of the command's payload keys,
# parameters amd req_priv_list from a string to a list. If they are None,
# they are converted to an empty list.
def convert_command_values_to_list(command):
    for key in ['payload_keys', 'request_parameters', 'req_priv_list']:
        command[key] = normalize_value(command.get(key))
    return command

@action(base_route + "onboard_form", method=["GET", "POST"])
@action.uses(db, session, T, "module_onboarding/onboard_form.html")
def onboard_form():
    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('description', requires=IS_NOT_EMPTY()),
        Field('gateway_url', requires=IS_NOT_EMPTY())
    ]
    module_form = Form(fields, formstyle=FormStyleBulma)

    # Get the community module type id
    module_type_id = get_community_module_type_id()

    if module_form.accepted:
        # Add the module type id to the form
        module_form.vars.module_type_id = module_type_id
        
        # Print the form variables
        print(module_form.vars)

        # Check if the module exists with the given module name
        module = db(db.modules.name == module_form.vars.name).select().first()

        # Check if the module exists
        if module:
            # Print a response flash
            response.flash = 'Module already exists. Please choose a different name.'
        else:
            # Insert the module form into the database
            module_id = db.modules.insert(**module_form.vars)

            # Set the module id in the session
            session.module_id = module_id

            # Redirect to the manage commands page
            redirect(URL('manage_commands', vars=dict(module_id=module_id)))

            # Print a response flash
            response.flash = 'Form accepted'
    elif module_form.errors:
        response.flash = 'Form has errors. Please fill out the form'
    
    return dict(module_form=module_form)

@action(base_route + "manage_commands", method=["GET", "POST"])
@action.uses(db, session, T, "module_onboarding/manage_commands.html")
def manage_commands():
    # Set a flag to be used by the UI to determine if the form should be displayed
    show_form = True

    # Check if the module id is in the URL parameters
    if 'module_id' not in request.vars:
        # Redirect to the module onboarding page
        logging.warning("No module id in the URL. Redirecting...")
        redirect(URL('module_onboarding', 'onboard_form'))

    # Get the module id from the URL
    module_id = request.vars['module_id']

    # Get the module from the database
    module = db(db.modules.id == module_id).select().first()

    # Check if the module exists
    if not module:
        # Redirect to the module onboarding page
        logging.warning("Module does not exist. Redirecting...")
        redirect(URL('module_onboarding', 'onboard_form'))

    fields = [
        Field('command_name', requires=IS_NOT_EMPTY()),
        Field('action_url', requires=IS_NOT_EMPTY()),
        Field('request_method', requires=IS_NOT_EMPTY()),
        Field('request_parameters', requires=IS_NOT_EMPTY()),
        Field('payload_keys', requires=IS_NOT_EMPTY()),
        Field('req_priv_list', requires=IS_NOT_EMPTY()),
        Field('description', requires=IS_NOT_EMPTY())
    ]
    command_form = Form(fields, formstyle=FormStyleBulma)

    # Create a grid to display the commands
    command_grid = db(db.module_commands.module_id == module_id).select()

    # Check if the form is valid
    if command_form.accepted:
        # Transform the command_name into a key
        command_form.vars.command_name = convert_command_to_key(command_form.vars.command_name)

        # Convert the command values to a list
        command_form.vars = convert_command_values_to_list(command_form.vars)

        # Add the 'community_name' payload key to the form var payload_keys list. Check if it is a string first.
        command_form.vars.payload_keys.append('community_name')

        # Insert the command form into the database
        exists_flag = insert_command(module_id, command_form.vars)

        # Refresh the grid
        command_grid = db(db.module_commands.module_id == module_id).select()
    elif command_form.errors:
        response.flash = 'Form has errors. Please fill out the form'

    return dict(show_form=show_form, command_form=command_form, command_grid=command_grid)