# -*- coding: utf-8 -*-
import json


# try something like
def index(): return dict(message="hello from identity_label.py")

# A helper function to parse the payload of a request.
def parse_payload():
    payload = request.body.read()
    if not payload:
        raise ValueError("No payload given.")
    return payload

# Function to create a new identity label for a given identity_name and community_name.
# Throws an error if no identity_name or community_name is given, or the identity label already exists.
# Also throws an error if the identity or the community does not exist.
def create():
    # Define the payload.
    try:
        payload = parse_payload()
    except ValueError as e:
        return dict(msg=str(e))
    
    payload = json.loads(payload)
    
    # Check if the payload has the required fields identity name, community name and label.
    if 'identity_name' not in payload or 'community_name' not in payload or 'label' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Check if the identity label already exists.
    if db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).count() > 0:
        return dict(msg="Identity label already exists.")
    
    # Insert the identity label.
    db.identity_labels.insert(identity_id=identity.id, community_id=community.id, label=payload['label'])

    return dict(msg="Identity label created.")

# Get all identity labels for a given identity name and community name in a payload object.
def get_by_identity_and_community():
    # Define the payload.
    try:
        payload = parse_payload()
    except ValueError as e:
        return dict(msg=str(e))
    
    payload = json.loads(payload)
    
    # Check if the payload has the required fields identity name and community name.
    if 'identity_name' not in payload or 'community_name' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")

    # Get all identity labels for the given identity name and community name.
    identity_labels = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select()
    
    return dict(data=identity_labels)

# Function to update an identity label for a given identity name and community name.
# Throws an error if no identity name, community name or label is given, or the identity label does not exist.
def update_by_identity_and_community():
    # Define the payload.
    try:
        payload = parse_payload()
    except ValueError as e:
        return dict(msg=str(e))
    
    payload = json.loads(payload)
    
    # Check if the payload has the required fields identity name, community name and label.
    if 'identity_name' not in payload or 'community_name' not in payload or 'label' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Check if the identity label exists.
    identity_label = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select().first()
    if not identity_label:
        return dict(msg="Identity label does not exist.")
    
    # Update the identity label.
    identity_label.update_record(label=payload['label'])
    
    return dict(msg="Identity label updated.")

# Function to delete an identity label for a given identity name and community name.
# Throws an error if no identity name or community name is given, or the identity label does not exist.
def delete_by_identity_and_community():
    # Define the payload.
    try:
        payload = parse_payload()
    except ValueError as e:
        return dict(msg=str(e))
    
    payload = json.loads(payload)
    
    # Check if the payload has the required fields identity name and community name.
    if 'identity_name' not in payload or 'community_name' not in payload:
        return dict(msg="Payload missing required fields.")
    
    # Check if the identity exists.
    identity = db(db.identities.name == payload['identity_name']).select().first()
    if not identity:
        return dict(msg="Identity does not exist.")
    
    # Check if the community exists.
    community = db(db.communities.community_name == payload['community_name']).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    
    # Check if the identity label exists.
    identity_label = db((db.identity_labels.identity_id == identity.id) & (db.identity_labels.community_id == community.id)).select().first()
    if not identity_label:
        return dict(msg="Identity label does not exist.")
    
    # Delete the identity label.
    identity_label.delete_record()
    
    return dict(msg="Identity label deleted.")
