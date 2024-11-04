# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from communities_modules.py")

def get_identity(identity_name):
    return db(db.identities.name == identity_name).select().first()

# A helper function that checks if a given identity exists in a given community. Returns True if the identity exists in the community, False otherwise.
def identity_in_community(identity_name, community_name):
    identity = db(db.identities.name == identity_name).select(db.identities.id).first()
    community = db(db.communities.community_name == community_name).select(db.communities.id).first()
    
    if not identity or not community:
        return False
    
    membership = db((db.community_members.identity_id == identity.id) &
                    (db.community_members.community_id == community.id)).select().first()
    
    return bool(membership)

# A helper function that checks if a given identity is an admin of a given community. Returns True if the identity is an admin, False otherwise.
def identity_is_admin(identity_name, community_name):
    identity = db(db.identities.name == identity_name).select(db.identities.id).first()
    community = db(db.communities.community_name == community_name).select(db.communities.id).first()
    
    if not identity or not community:
        return False
    
    membership = db((db.community_members.identity_id == identity.id) &
                    (db.community_members.community_id == community.id)).select().first()
    if not membership:
        return False
    role = db(db.roles.id == membership.role_id).select().first()
    return role.name in ['Admin', 'Owner', 'admin', 'owner']

def is_community_module(module):
    module_type = db(db.module_types.id == module.module_type_id).select().first()
    return module_type.name == "Community"

# Get all community modules accross all communities.
def get_all():
    community_modules = db(db.community_modules).select()
    return dict(data=community_modules)

# Get all community modules in a given community id.
def get_by_community_id():
    community_id = request.args(0)
    if not community_id:
        return dict(msg="No community id given.")
    community_modules = db(db.community_modules.community_id == community_id).select()
    return dict(data=community_modules)

# Get a community module by its community id and module id. If the community module does not exist, return an error.
def get_by_community_id_and_module_id():
    community_id = request.args(0)
    module_id = request.args(1)
    if not community_id or not module_id:
        return dict(msg="No community id or module id given.")
    community_module = db((db.community_modules.community_id == community_id) & (db.community_modules.module_id == module_id)).select().first()
    if not community_module:
        return dict(msg="Community module is not installed in this community.")
    return dict(community_module=community_module)

# Get a community module by its community name and module id. If the community module does not exist, return an error.
def get_by_community_name_and_module_id():
    community_name = request.args(0)
    module_id = request.args(1)
    if not community_name or not module_id:
        return dict(msg="No community name or module id given.")
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    community_module = db((db.community_modules.community_id == community.id) & (db.community_modules.module_id == module_id)).select().first()
    if not community_module:
        return dict(msg="Community module is not installed in this community.")
    return community_module.as_dict()

# Update a community module by its community id and module id. If the community module does not exist, return an error.
def update_by_community_id_and_module_id():
    community_id = request.args(0)
    module_id = request.args(1)
    if not community_id or not module_id:
        return dict(msg="No community id or module id given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'module_id' not in payload or 'community_id' not in payload or 'enabled' not in payload or 'priv_list' not in payload:
        return dict(msg="Payload missing required fields.")
    community_module = db((db.community_modules.community_id == community_id) & (db.community_modules.module_id == module_id)).select().first()
    if not community_module:
        return dict(msg="Community module does not exist.")
    community_module.update_record(**payload)
    return dict(msg="Community module updated.")

# Delete a community module by its community id and module id. If the community module does not exist, return an error.
def delete_by_community_id_and_module_id():
    community_id = request.args(0)
    module_id = request.args(1)
    if not community_id or not module_id:
        return dict(msg="No community id or module id given.")
    community_module = db((db.community_modules.community_id == community_id) & (db.community_modules.module_id == module_id)).select().first()
    if not community_module:
        return dict(msg="Community module does not exist.")
    community_module.delete_record()
    return dict(msg="Community module deleted.")

# Install a community module, using its module_id in a payload, into a given community_name as an argument. If the community module already exists in the given community, return an error.
def install_by_community_name():
    community_name = request.args(0)
    payload = request.body.read()

    if not community_name or not payload:
        return dict(msg="Missing community name or payload.")

    payload = jloads(payload)
    if 'module_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields: module_name and identity_name.")

    # Combine queries for community, identity, module, and membership
    query = (db.communities.community_name == community_name) & \
            (db.identities.name == payload['identity_name']) & \
            (db.marketplace_modules.name == payload['module_name']) & \
            (db.community_members.community_id == db.communities.id) & \
            (db.community_members.identity_id == db.identities.id) & \
            (db.roles.id == db.community_members.role_id)

    result = db(query).select(db.communities.ALL, 
                              db.identities.ALL, 
                              db.marketplace_modules.ALL,
                              db.roles.name.with_alias('role_name')).first()

    if not result:
        return dict(msg="Invalid community, identity, or module, or identity is not a member of the community.")

    if result.communities.community_name == "Global":
        return dict(msg="Cannot install community module in Global community.")

    if result.role_name not in ['Admin', 'Owner', 'admin', 'owner']:
        return dict(msg="Identity is not an admin of the community.")

    module_type = db(db.module_types.id == result.marketplace_modules.module_type_id).select(db.module_types.name).first()
    if module_type.name != "Community":
        return dict(msg="This operation is only allowed for Community modules.")

    existing_module = db((db.community_modules.community_id == result.communities.id) & 
                         (db.community_modules.module_id == result.marketplace_modules.id)).select().first()
    if existing_module:
        return dict(msg="This module is already installed in this community.")

    new_module = {
        'module_id': result.marketplace_modules.id,
        'community_id': result.communities.id,
        'enabled': payload.get('enabled', True),
        'privilages': payload.get('privilages', [])
    }
    db.community_modules.insert(**new_module)
    return dict(msg="Community module installed.")

# Uninstall a community module, using its module_id in a payload, from a given community_name as an argument. If the community module does not exist in the given community, return an error.
def uninstall_by_community_name():
    community_name = request.args(0)
    payload = request.body.read()

    if not community_name:
        return dict(msg="No community name given.")
    if not payload:
        return dict(msg="No payload given.")
    
    # Check if the payload contains the module_name  and identity_name fields
    payload = jloads(payload)
    if 'module_name' not in payload or 'identity_name' not in payload:
        return dict(msg="Payload missing required fields. Please provide module_name and identity_name fields.")
    
    # Combine queries for community, identity, and module
    community = db(db.communities.community_name == community_name).select().first()
    identity = db(db.identities.name == payload['identity_name']).select().first()
    module = db(db.marketplace_modules.name == payload['module_name']).select().first()

    if not all([community, identity, module]):
        return dict(msg="Invalid community, identity, or module.")

    if community.community_name == "Global":
        return dict(msg="Cannot install community module in Global community.")

    if not identity_in_community(payload['identity_name'], community_name):
        return dict(msg="Identity is not a member of the community.")

    if not identity_is_admin(payload['identity_name'], community_name):
        return dict(msg="Identity is not an admin of the community.")

    # Check that the module exists
    community_module = db((db.community_modules.community_id == community.id) & (db.community_modules.module_id == module.id)).select().first()
    
    if not community_module:
        return dict(msg="Community module does not exist.")

    community_module.delete_record()
    return dict(msg="Community module uninstalled.")
