# This script initializes additional functionality of the DB after the tables have been created.

# Import the necessary modules python modules
from pydal import DAL
from py4web.utils.auth import Auth
from json import load as jload
import logging
import os

# Import the necessary dataclasses from the Waddlebot-libs module
# Might need to change the name of the module to Waddlebot_libs, because python is case sensitive
from ..modules.libs.botClasses import module_command_metadata


# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)

# Set the base URL to find all the default data files
base_url = os.path.join(os.getcwd(), "apps/WaddleDBM/default_data")

# Class to initialize the DB
class db_initializer:
    # Constructor
    def __init__(self, db: DAL, auth: Auth):
        self.db = db
        self.auth = auth

    # Method to initialize the DB
    def init_db(self):
        self.create_global_community()

        # Using the create_default_data helper function, insert the default data into the tables.

        # Run the test command
        # logging.warning("=====================================")
        # self.test_get_commands("{base_url}/default_commands/admin_context.json")
        # logging.warning("=====================================")

        testcurrentpath = os.getcwd()

        print("Current path: ", testcurrentpath)

        testparentpath = os.path.dirname(testcurrentpath)

        print("Parent path: ", testparentpath)

        # Create the default data for the prize_statuses table
        # self.create_default_data(f"{base_url}/default_prize_statuses.json", "prize_statuses", "status_name")
        self.create_default_data(os.path.join(base_url, "default_prize_statuses.json"), "prize_statuses", "status_name")

        # Create the default data for the module_types table
        # self.create_default_data(f"{base_url}/default_module_types.json", "module_types", "name")
        self.create_default_data(os.path.join(base_url, "default_module_types.json"), "module_types", "name")

        # Create the default data for the core modules
        # self.create_default_data(f"{base_url}/core_modules.json", "modules", "name")
        self.create_default_data(os.path.join(base_url, "core_modules.json"), "modules", "name")

        # After creating the core modules, create the module_commands for each module.
        # self.init_module_commands(f"{base_url}/default_commands/")
        self.init_module_commands(os.path.join(base_url, "default_commands/"))

        # Create the default data for the account types
        # self.create_default_data(f"{base_url}/default_account_types.json", "account_types", "type_name")
        self.create_default_data(os.path.join(base_url, "default_account_types.json"), "account_types", "type_name")

        # Create the default data for the gateway server types
        # self.create_default_data(f"{base_url}/default_gateway_server_types.json", "gateway_server_types", "type_name")
        self.create_default_data(os.path.join(base_url, "default_gateway_server_types.json"), "gateway_server_types", "type_name")

        # Create the default data for the gateway types
        # self.create_default_data(f"{base_url}/default_gateway_types.json", "gateway_types", "type_name")
        self.create_default_data(os.path.join(base_url, "default_gateway_types.json"), "gateway_types", "type_name")

        # Create the default data for the gateway accounts
        # self.create_default_data(f"{base_url}/default_gateway_accounts.json", "gateway_accounts", "account_name")
        self.create_default_data(os.path.join(base_url, "default_gateway_accounts.json"), "gateway_accounts", "account_name")

        # Create the default data for the gateway servers
        # self.create_default_data(f"{base_url}/default_gateway_servers.json", "gateway_servers", "name")
        self.create_default_data(os.path.join(base_url, "default_gateway_servers.json"), "gateway_servers", "name")

        # Create the default data for the routing gateways table
        # self.create_default_data(f"{base_url}/default_routing_gateways.json", "routing_gateways", "gateway_name")
        self.create_default_data(os.path.join(base_url, "default_routing_gateways.json"), "routing_gateways", "channel_id")

        # Create the default auth user
        self.create_default_user()

    
    # Test function to check if command files exist
    def test_get_commands(self, commands_directory: str):
        logging.warning("GETTING COMMANDS.....")
        try:
            with open(commands_directory, "r") as file:
                data = jload(file)
                print(data)

        except FileNotFoundError:
            logging.error("Core modules file not found. Unable to create core modules.")

    # A function to create the global community in the communities DB, if it doesnt exist, and create a routing entry for it
    def create_global_community(self):
        if self.db(self.db.communities.community_name == "Global").count() == 0:
            self.db.communities.insert(community_name="Global", community_description="The global community.")

            global_community = self.db(self.db.communities.community_name == "Global").select().first()
            if self.db(self.db.routing.community_id == global_community.id).count() == 0:
                self.db.routing.insert(channel="Global", community_id=global_community.id, gateways=[], aliases=[])

                self.db.commit()

            # Create the default roles for the global community.
            self.create_roles(global_community.id)

    # A function to create the default roles found in the roles table
    # A helper function to create a list of roles for a newly created community, using its community_id.
    # TODO: Figure out how to add the requirements field to the roles table and implement it.
    def create_roles(self, community_id: int):
        logging.warning("Creating default roles....")

        # Read the default roles from the default_roles.json file
        filePath = f"{base_url}/default_roles.json"

        roles = []

        try:
            with open(filePath, "r") as file:
                roles = jload(file)

        except FileNotFoundError:
            logging.error("Core modules file not found. Unable to create core modules.") 

        logging.warning("Found Default Roles:")
        logging.warning(roles)

        requirements = ["None"]

        for role in roles:
            name = role['role']
            description = role['description']
            priv_list = role['permissions']

            self.db.roles.insert(name=name, description=description, community_id=community_id, priv_list=priv_list, requirements=requirements)

        self.db.commit()


    # Function to create the default data for a given file_path, table and compare_column.
    # This function is used to insert default data into the initial tables.
    def create_default_data(self, file_path: str, table: str, compare_column: str):
        logging.warning(f"Creating default data for table {table}....")
        data = self.get_data(file_path)
        self.insert_data(table, data, compare_column)

    # Function to loop through the core modules, and create the module_commands for each module.
    def init_module_commands(self, commands_directory: str):
        logging.warning("Creating core modules....")

        core_modules = self.db(self.db.modules).select()

        for module in core_modules:
            self.create_commands_by_module(commands_directory, module.name)

    # Function that receives a module_name value, gets the module_id from the modules table, 
    # and gets the commands from the appropriate json file, and inserts them into the module_commands table.
    # The default module commands are found in the given commands folder directory variable. 
    # Each module has its own json file with the commands for that module, and the name of the file is the module_name.
    def create_commands_by_module(self, commands_directory: str, module_name: str):
        logging.warning(f"Creating module commands for module {module_name}....")

        try:
            module_id = self.db(self.db.modules.name == module_name).select().first().id

            file_path = f"{commands_directory}{module_name}.json"
            data = self.get_data(file_path)

            # logging.warning("=====================================")
            # logging.warning(f"FOUND DATA!!!:")
            # logging.warning(data)
            # logging.warning("=====================================")

            # Each command in the data is of type module_commands, which is a dataclass.

            # Set each command as a module_commands object, and insert it into the module_commands table.
            for command in data:
                command = {
                    "module_id": module_id,
                    "command_name": command['command_name'],
                    "description": command['description'],
                    "action_url": command['action_url'],
                    "request_method": command['request_method'],
                    "request_parameters": command['request_parameters'],
                    "payload_keys": command['payload_keys'],
                    "req_priv_list": command['req_priv_list'],
                    "req_param_amount": command['req_param_amount']
                }

                logging.warning("Command object set. Inserting into module_commands table....")
                logging.warning("Command object:")
                logging.warning(command)

                # Insert the command into the module_commands table.
                # Only do so if the command does not already exist in the table.
                if self.db(self.db.module_commands.command_name == command['command_name']).count() == 0:
                    self.db.module_commands.insert(
                        module_id=command['module_id'],
                        command_name=command['command_name'],
                        description=command['description'],
                        action_url=command['action_url'],
                        request_method=command['request_method'],
                        request_parameters=command['request_parameters'],
                        payload_keys=command['payload_keys'],
                        req_priv_list=command['req_priv_list'],
                        req_param_amount=command['req_param_amount']
                    )

                logging.warning("Command inserted into module_commands table.")
        # If the module is not found, log an error message.        
        except AttributeError:
            logging.error(f"Module {module_name} not found. Unable to create module commands.")

    # A helper function to retrieve data from a given json file, and return it as a list of dictionaries.
    def get_data(self, file_path: str):
        try:
            logging.warning(f"Retrieving data from file {file_path}....")
            with open(file_path, "r") as file:
                data = jload(file)

        except FileNotFoundError:
            logging.error(f"File {file_path} not found. Unable to retrieve data.") 
            return []

        return data

    # A helper function to insert given data, into a given table, if the data does not already exist.
    def insert_data(self, table: str, data: list, compare_column: str):
        # Log the table that the data is being inserted into
        logging.warning(f"Inserting data into table {table}....")

        if not self.db[table]:
            logging.error(f"Table {table} does not exist. Unable to insert data.")
            return

        if not data:
            logging.error("Data list is empty. Unable to insert data.")
            return
        
        logging.warning(f"Found data to insert:")
        logging.warning(data)

        for entry in data:
            if self.db(self.db[table][compare_column] == entry[compare_column]).count() == 0:
                self.db[table].insert(**entry)

        self.db.commit()

    # A function to create a new default auth user, if it does not already exist.
    # This user information is extracted from the OS environment variables.
    def create_default_user(self) -> None:
        logging.warning("Creating default user....")

        default_user = os.getenv("DEFAULT_USER")
        default_password = os.getenv("DEFAULT_PASSWORD")
        default_email = os.getenv("DEFAULT_EMAIL")

        if not default_user or not default_password or not default_email:
            logging.error("Default user information not found in environment variables. Unable to create default user.")
            return

        if self.db(self.db.auth_user.email == default_email).count() == 0:
            logging.warning("Default user not found. Creating default user....")
            user_data = {
                'username': default_user,
                'email': default_email,
                'password': default_password,
                'first_name': "Test",
                'last_name': "User"
            }
            result = self.auth.register(user_data)
            if result.get('errors'):
                logging.error(f"Error creating default user: {result['errors']}")
            else:
                self.db.commit()
                logging.info("Default user created successfully.")
        else:
            logging.info("Default user already exists.")

    