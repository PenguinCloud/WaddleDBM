"""
This file defines the database models
"""

from pydal.validators import *

from .common import Field, db


# Import the db initializer script from scripts/db_initialization.py
from .scripts.init_db import db_initializer

# Import the helper functions from the modules
from .modules.WaddlebotLibs.botDBMHelpers import dbm_helpers

# Import the matterbridge helper functions
from .modules.WaddlebotLibs.botMatterbridgeHelpers import matterbridge_helpers

# Import the BotLogger class from the WaddlebotLibs botLogger scripts module
from .modules.WaddlebotLibs.botLogger import BotLogger

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#

db.define_table('thing', Field('name'))

# Define the module types table
db.define_table('module_types',
                Field('name', 'string'),
                Field('description', 'string'))

# Define the modules table
db.define_table('modules', 
                Field('name', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string', requires=IS_NOT_EMPTY()),
                Field('module_type_id', db.module_types))

# Define the module metadata table.
# db.define_table('modules_metadata',
#                 Field('module_id', db.modules),
#                 Field('command', 'string', requires=IS_NOT_EMPTY()),
#                 Field('action', 'string', requires=IS_NOT_EMPTY()),
#                 Field('help_text', 'string', requires=IS_NOT_EMPTY()),
#                 Field('method', 'string', requires=IS_NOT_EMPTY()),
#                 Field('req_priv_list', 'list:string'))

# Define the module metadata table.
db.define_table('module_commands',
                Field('module_id', db.modules),
                Field('command_name', 'string', requires=IS_NOT_EMPTY()),
                Field('action_url', 'string', requires=IS_NOT_EMPTY()),
                Field('description', 'string', requires=IS_NOT_EMPTY()),
                Field('request_method', 'string', requires=IS_NOT_EMPTY()),
                Field('request_parameters', 'list:string'),
                Field('payload_keys', 'list:string'),
                Field('req_priv_list', 'list:string'))

# Define the identities table
db.define_table('identities', 
                Field('name', 'string'),
                Field('country', 'string'),
                Field('ip_address', 'string'),
                Field('browser_fingerprints', 'list:string'),
                Field('reputation', 'integer', default=0))

# Define the communities table
db.define_table('communities', 
                Field('community_name'),
                Field('community_description'))

# Define a table that keeps track of labels for identities in a community
db.define_table('identity_labels',
                Field('identity_id', db.identities),
                Field('community_id', db.communities),
                Field('label', 'string'))

# Define table for community modules
db.define_table('community_modules', 
                Field('module_id', db.modules),
                Field('community_id', db.communities),
                Field('enabled', 'boolean', default=True),
                Field('priv_list', 'list:string'))

# Define a table for roles
db.define_table('roles',
                Field('name', 'string'),
                Field('community_id', db.communities),
                Field('description', 'string'),
                Field('priv_list', 'list:string'),
                Field('requirements', 'list:string'))

# Define a table for community members table
db.define_table('community_members', 
                Field('community_id', db.communities),
                Field('identity_id', db.identities),
                Field('role_id', db.roles))
                # Field('currency', 'integer', default=0),
                # Field('reputation', 'integer', default=0))

# Define a table to store the reputation of a user, per community
db.define_table('reputation',
                Field('community_id', db.communities),
                Field('identity_id', db.identities),
                Field('amount', 'integer', default=0))

# Define a table that stores the currency of a user, per community
db.define_table('currency',
                Field('community_id', db.communities),
                Field('identity_id', db.identities),
                Field('amount', 'integer', default=0))

# Define a table that contains different gateway server types
db.define_table('gateway_server_types',
                Field('type_name', 'string'),
                Field('description', 'string'))


# Define a table that keeps track of gateway servers
db.define_table('gateway_servers', 
                Field('name', 'string'),
                Field('server_id', 'string'),
                Field('server_nick', 'string'),
                Field('server_type', db.gateway_server_types),
                Field('protocol', 'string'))


# Define a table that maps specific gateways to a community through an ID
db.define_table('routing', 
                Field('channel', 'string'),
                Field('community_id', db.communities),
                Field('routing_gateway_ids', 'list:integer'),
                Field('aliases', 'list:string'))


# Define a table that binds an identity to a community namespace through an ID, as a context. Every identity can only be in one community namespace at a time
db.define_table('context', 
                Field('identity_id', db.identities),
                Field('community_id', db.communities))

# Define a table that stores matterbridge account types
db.define_table('account_types',
                Field('type_name', 'string'),
                Field('description', 'string'))

# Define a table that stores matterbridge account types
db.define_table('gateway_accounts',
                Field('account_name', 'string'),
                Field('account_type', db.account_types),
                Field('is_default', 'boolean', default=False))

# Define a table that stores routing gateway types
db.define_table('gateway_types',
                Field('type_name', 'string'),
                Field('description', 'string'))

# Define a table that keeps track of routing gateways for the creation of the matterbridge configuration file
db.define_table('routing_gateways',
                Field('gateway_server', db.gateway_servers),
                Field('channel_id', 'string'),
                Field('gateway_type', db.gateway_types),
                Field('activation_key', 'string'),
                Field('is_active', 'boolean', default=False))

# Define a table that stores calendar events, per community
db.define_table('calendar',
                Field('community_id', db.communities),
                Field('event_name', 'string'),
                Field('event_description', 'string'),
                Field('event_start', 'datetime'),
                Field('event_end', 'datetime'),
                Field('not_start_sent', 'boolean', default=False),
                Field('not_end_sent', 'boolean', default=False))

# Define a table that stores an admin context session for a community, per identity
db.define_table('admin_contexts',
                Field('identity_id', db.identities),
                Field('community_id', db.communities),
                Field('session_token', 'string'),
                Field('session_expires', 'datetime'))

# Define a table that maps a text value to a response value, per community
db.define_table('text_responses',
                Field('community_id', db.communities),
                Field('text_val', 'string'),
                Field('response_val', 'string'))

# Define a table that keeps track of prize statuses
db.define_table('prize_statuses',
                Field('status_name', 'string'),
                Field('description', 'string'))

# Define a table that stores prizes, per community
db.define_table('prizes',
                Field('community_id', db.communities),
                Field('prize_guid', 'string'),
                Field('prize_name', 'string'),
                Field('prize_description', 'string'),
                Field('winner_identity_id', db.identities, default=None),
                Field('prize_status', db.prize_statuses),
                Field('timeout', 'integer', default=0))

# Define a table that stores all the users that have entered a prize draw
db.define_table('prize_entries',
                Field('prize_id', db.prizes),
                Field('identity_id', db.identities))

# Define a table that maps an alias to specific command for a community
db.define_table('alias_commands',
                Field('community_id', db.communities),
                Field('alias_val', 'string'),
                Field('command_val', 'string'))

db.commit()

# #######################################################
# Define the helper functions
# #######################################################

# Create a DB initializer object
db_init = db_initializer(db)

# Create a WaddleDBM_Helpers object
waddle_helpers = dbm_helpers(db)

# Create a Matterbridge_Helpers object
mat_helpers = matterbridge_helpers(db)

# Create a BotLogger object
waddleLogger = BotLogger()

# Initialize the DB
db_init.init_db()