# -*- coding: utf-8 -*-
import json
import logging


# try something like
def index(): return dict(message="hello from module onboarding.py")

# set the logging level to info
logging.basicConfig(level=logging.INFO)

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
    logging.info("Inserting command into the database...")
    flag = False
    # Check if the command object is not empty and if it already exists in the database
    if command and not db((db.module_commands.command_name == command['command_name'])).select().first():
        # Insert the command object into the database
        db.module_commands.insert(module_id=module_id, **command)
        # Print a response flash
        response.flash = 'New command has been added to your module.'
    else:
        logging.info("Command already exists in the database. Skipping...")
        # Print a response flash
        response.flash = 'This command already exists. Please check the command name.'
        flag = True

    return flag

# Helper function to retrieve a list of commands from the module_commands table
def get_commands(module_id):
    logging.info("Getting commands from the database...")
    return db(db.module_commands.module_id == module_id).select()

# Helper function to check if a given command name already exists in the given metadata object as a key
def command_exists_in_metadata(command_name, metadata):
    logging.info("Checking if command exists in metadata...")
    return command_name in metadata

# Helper function to check if the command object contains all the required fields
def command_object_is_valid(command):
    logging.info("Checking if command object is valid...")
    return 'command_name' in command and 'action_url' in command and 'request_method' in command and 'request_parameters' in command and 'payload_keys' in command and 'req_priv_list' in command and 'description' in command

# Function to add a command object to the metadata of a module. This command object is received from the form
def add_command_to_metadata(command_list: list, metadata: dict) -> dict:
    logging.info("Adding command to metadata...")
    # Check if the post request is not empty
    if len(command_list) > 0:
        for command in command_list:
            if command_object_is_valid(command) and not command_exists_in_metadata(command['command_name'], metadata):
                # Get the values from the form
                metadata[command['command_name']] = {
                    "action": command['action_url'],
                    "description": command['description'],
                    "method": command['request_method'],
                    "parameters": command['request_parameters'],
                    "payload_keys": command['payload_keys'],
                    "req_priv_list": command['req_priv_list']
                }

    return metadata

# Helper function to convert a given command string into a command string 
# that can be used as a key in the metadata object, but replacing spaces 
# with underscores and adding a # at the start.
def convert_command_to_key(command):
    # Check if the first character starts with a # or !. If not, add a #
    if command[0] != "#" and command[0] != "!":
        command = "#" + command
    return command.replace(" ", "_")

# Helper function to convert the instances of the command's payload keys,
# parameters amd req_priv_list from a string to a list. If they are None,
# they are converted to an empty list.
def convert_command_values_to_list(command):
    # Check if the command object is not empty
    if command:
        # Convert the none values to an empty list
        if command['payload_keys'] is None:
            command['payload_keys'] = []
        elif isinstance(command['payload_keys'], str):
            command['payload_keys'] = [command['payload_keys']]
        
        if command['request_parameters'] is None:
            command['request_parameters'] = []
        elif isinstance(command['request_parameters'], str):
            command['request_parameters'] = [command['request_parameters']]

        if command['req_priv_list'] is None:
            command['req_priv_list'] = []
        elif isinstance(command['req_priv_list'], str):
            command['req_priv_list'] = [command['req_priv_list']]                                   

    return command

def onboard_form():
    module_form = SQLFORM(db.marketplace_modules, fields=['name', 'description', 'gateway_url'])

    # Get the community module type id
    module_type_id = get_community_module_type_id()

    if module_form.validate():
        # Add the module type id to the form
        module_form.vars.module_type_id = module_type_id
        
        # Print the form variables
        print(module_form.vars)

        # Check if the module exists with the given module name
        module = db(db.marketplace_modules.name == module_form.vars.name).select().first()

        # Check if the module exists
        if module:
            # Print a response flash
            response.flash = 'Module already exists. Please choose a different name.'
        else:
            # Insert the module form into the database
            module_id = db.marketplace_modules.insert(**module_form.vars)

            # Set the module id in the session
            session.module_id = module_id

            # Redirect to the manage commands page
            redirect(URL('manage_commands', vars=dict(module_id=module_id)))

            # Print a response flash
            response.flash = 'Form accepted'
    elif module_form.errors:
        response.flash = 'Form has errors. Please fill out the form'
    
    return dict(module_form=module_form)

# Function to add a command to a given module id, found in the arguments of the URL
def manage_commands():
    # Set a flag to be used by the UI to determine if the form should be displayed
    show_form = True

    # Check if the module id is in the URL parameters
    if 'module_id' not in request.vars:
        # Redirect to the module onboarding page
        logging.info("No module id in the URL. Redirecting...")
        redirect(URL('module_onboarding', 'onboard_form'))

    # Get the module id from the URL
    module_id = request.vars['module_id']

    # Get the module from the database
    module = db(db.marketplace_modules.id == module_id).select().first()

    # Check if the module exists
    if not module:
        # Redirect to the module onboarding page
        logging.info("Module does not exist. Redirecting...")
        redirect(URL('module_onboarding', 'onboard_form'))

    # Create an sql form from the sql form factory to create a form for the user to input the command details
    command_form = SQLFORM.factory(db.module_commands, fields=['command_name', 'action_url', 'request_method', 'request_parameters', 'payload_keys', 'req_priv_list', 'description'])

    # Create a grid to display the commands
    command_grid = SQLFORM.grid(db.module_commands.module_id == module_id, create=False, editable=True, deletable=True)

    # Check if the form is valid
    if command_form.validate():
        # Transform the command_name into a key
        command_form.vars.command_name = convert_command_to_key(command_form.vars.command_name)

        # Convert the command values to a list
        command_form.vars = convert_command_values_to_list(command_form.vars)

        # Add the 'community_name' payload key to the form var payload_keys list. Check if it is a string first.
        command_form.vars.payload_keys.append('community_name')

        # Insert the command form into the database
        exists_flag = insert_command(module_id, command_form.vars)

        # Set the command variable to the form variables
        command_list = get_commands(module_id)

        # Get the metadata from the module
        metadata = {}

        # Check if the metadata is not empty  
        if module.metadata:
            # Load the metadata from the module
            metadata = module.metadata

        if not exists_flag:
            # Get the command object from the form
            newMetadata = add_command_to_metadata(command_list=command_list, metadata=metadata)

            # Update the module metadata
            module.update_record(metadata=newMetadata)

        # Refresh the grid
        command_grid = SQLFORM.grid(db.module_commands.module_id == module_id, create=False, editable=True, deletable=True)
    elif command_form.errors:
        response.flash = 'Form has errors. Please fill out the form'

    return dict(show_form=show_form, command_form=command_form, command_grid=command_grid)
