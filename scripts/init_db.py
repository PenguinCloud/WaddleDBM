# This script initializes additional functionality of the DB after the tables have been created.

# Import the necessary modules python modules
from pydal import DAL
from json import load as jload
import logging

# Import the necessary dataclasses from the Waddlebot-libs module
# Might need to change the name of the module to Waddlebot_libs, because python is case sensitive
from importlib import import_module

# Import the necessary dataclasses from the Waddlebot-libs module
module = import_module("applications.WaddleDBM.Waddlebot-libs.botClasses").module
module_command_metadata = import_module("applications.WaddleDBM.Waddlebot-libs.botClasses").module_command_metadata

# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)

# Class to initialize the DB
class db_initializer:
    # Constructor
    def __init__(self, db: DAL):
        self.db = db

    # Method to initialize the DB
    def init_db(self):
        self.create_global_community()

        # Using the create_default_data helper function, insert the default data into the tables.

        # Create the default data for the prize_statuses table
        self.create_default_data("applications/WaddleDBM/models/default_prize_statuses.json", "prize_statuses", "status_name")

        # Create the default data for the module_types table
        self.create_default_data("applications/WaddleDBM/models/default_module_types.json", "module_types", "name")

        # Create the default data for the core modules
        self.create_default_data("applications/WaddleDBM/models/core_modules.json", "modules", "name")

        # Create the default data for the account types
        self.create_default_data("applications/WaddleDBM/models/default_account_types.json", "account_types", "type_name")

        # Create the default data for the gateway server types
        self.create_default_data("applications/WaddleDBM/models/default_gateway_server_types.json", "gateway_server_types", "type_name")

        # Create the default data for the gateway types
        self.create_default_data("applications/WaddleDBM/models/default_gateway_types.json", "gateway_server_types", "type_name")

        # Create the default data for the gateway accounts
        self.create_default_data("applications/WaddleDBM/models/default_gateway_accounts.json", "gateway_accounts", "account_name")

        # Create the default data for the gateway servers
        self.create_default_data("applications/WaddleDBM/models/default_gateway_servers.json", "gateway_servers", "name")

    
    # A function to create the global community in the communities DB, if it doesnt exist, and create a routing entry for it
    def create_global_community(self):
        if self.db(self.db.communities.community_name == "Global").count() == 0:
            self.db.communities.insert(community_name="Global", community_description="The global community.")

            global_community = self.db(self.db.communities.community_name == "Global").select().first()
            if self.db(self.db.routing.community_id == global_community.id).count() == 0:
                self.db.routing.insert(channel="Global", community_id=global_community.id, gateways=[], aliases=[])

            # Create the default roles for the global community.
            self.create_roles(global_community.id)

    # A function to create the default roles found in the roles table
    # A helper function to create a list of roles for a newly created community, using its community_id.
    # TODO: Figure out how to add the requirements field to the roles table and implement it.
    def create_roles(self, community_id: int):

        # Read the default roles from the default_roles.json file
        filePath = "applications/WaddleDBM/models/default_roles.json"

        try:
            with open(filePath, "r") as file:
                roles = jload(file)

        except FileNotFoundError:
            logging.error("Core modules file not found. Unable to create core modules.") 

        requirements = ["None"]

        for role in roles:
            name = role['role']
            description = role['description']
            priv_list = role['permissions']

            self.db.roles.insert(name=name, description=description, community_id=community_id, priv_list=priv_list, requirements=requirements)


    # Function to create the default data for a given file_path, table and compare_column.
    # This function is used to insert default data into the initial tables.
    def create_default_data(self, file_path: str, table: str, compare_column: str):
        data = self.get_data(file_path)
        self.insert_data(table, data, compare_column)
        

    # A helper function to retrieve data from a given json file, and return it as a list of dictionaries.
    def get_data(self, file_path: str):
        try:
            with open(file_path, "r") as file:
                data = jload(file)

        except FileNotFoundError:
            logging.error(f"File {file_path} not found. Unable to retrieve data.") 
            return []

        return data

    # A helper function to insert given data, into a given table, if the data does not already exist.
    def insert_data(self, table: str, data: list, compare_column: str):
        # Log the table that the data is being inserted into
        logging.info(f"Inserting data into table {table}....")

        if not self.db[table]:
            logging.error(f"Table {table} does not exist. Unable to insert data.")
            return

        if not data:
            logging.error("Data list is empty. Unable to insert data.")
            return

        for entry in data:
            if self.db(self.db[table][compare_column] == entry[compare_column]).count() == 0:
                self.db[table].insert(**entry)

    