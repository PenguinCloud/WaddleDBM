# -*- coding: utf-8 -*-
from json import loads as jloads


# try something like
def index(): return dict(message="hello from routing.py")

# Create a new routing from a given payload. Throws an error if no payload is given, or the routing already exists.
def create_routing():
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'name' not in payload or 'description' not in payload or 'priv_list' not in payload or 'requirements' not in payload:
        return dict(msg="Payload missing required fields.")
    if db(db.routing.name == payload['name']).count() > 0:
        return dict(msg="Routing already exists.")
    db.routing.insert(**payload)
    return dict(msg="Routing created.")

# Get all routings.
def get_all():
    routings = db(db.routing).select()
    return dict(data=routings)

# Function to get all routes that also have a community name.
def get_all_community_routes():
    routings = db(db.routing).select()
    for routing in routings:
        community = db(db.communities.id == routing.community_id).select().first()
        routing.community_name = community.community_name
    return dict(data=routings)

# Get a routing by its name. If the routing does not exist, return an error.
def get_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    routing = db(db.routing.name == name).select().first()
    if not routing:
        return dict(msg="Routing does not exist.")
    return dict(data=routing)

# Update a routing by its name. If the routing does not exist, return an error.
def update_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    payload = request.body.read()
    if not payload:
        return dict(msg="No payload given.")
    payload = jloads(payload)
    if 'name' not in payload or 'description' not in payload or 'priv_list' not in payload or 'requirements' not in payload:
        return dict(msg="Payload missing required fields.")
    routing = db(db.routing.name == name).select().first()
    if not routing:
        return dict(msg="Routing does not exist.")
    
    routing.update_record(**payload)
    return dict(msg="Routing updated.")

# Delete a routing by its name. If the routing does not exist, return an error.
def delete_by_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    routing = db(db.routing.name == name).select().first()
    if not routing:
        return dict(msg="Routing does not exist.")
    routing.delete_record()
    return dict(msg="Routing deleted.")

# Get all routings for a specific community name.
def get_by_community_name():
    name = request.args(0)
    name = waddle_helpers.decode_name(name)
    if not name:
        return dict(msg="No name given.")
    community = db(db.communities.community_name == name).select().first()
    if not community:
        return dict(msg="Community does not exist.")
    routings = db(db.routing.community_id == community.id).select()
    return dict(data=routings)



# Add a routing gateway to a community's list of gateways, if it doesnt exist, by their community name. If the community or 
# routing does not exist, return an error. The  is passed as an argument. The community_name is passed as a payload.
def add_route_to_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    channel_id = payload["channel_id"]
    account = payload["account"]
    command_str_list = payload['command_string']
    
    # Set the community name to the first element of the command_str_list.
    community_name = command_str_list[0]

    # Get the community
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)

    # Get the routing record from the routing table by the community_id. If it doesnt exist, create it.
    routing = db(db.routing.community_id == community.id).select().first()
    if not routing:
        routing = db.routing.insert(community_id=community.id)

    # Add the routing gateway to the routing record. By adding 
    routing_gateway_ids = routing.routing_gateway_ids
    if not routing_gateway_ids:
        routing_gateway_ids = []

    # Get the routing gateway by the channel_id and account.
    routing_gateway = waddle_helpers.get_routing_gateway(channel_id, account)

    # Check if the routing gateway is not null.
    if not routing_gateway:
        return dict(msg="Routing gateway does not exist. Please create it first via !gateway add [platform] [channel_name]")

    if routing_gateway.id in routing_gateway_ids:
        return dict(msg="Routing gateway already exists in community.")
    
    routing_gateway_ids.append(routing_gateway.id)
    routing.update_record(routing_gateway_ids=routing_gateway_ids)

    return dict(msg="Routing added to community.")

# Remove a routing gateway from a community's list of gateways, if it exists, by their community name. If the community or 
# routing does not exist, return an error. The channel ID is passed as an argument. The community_name is passed as a payload.
def remove_route_from_community():
    # Validate the payload, using the validate_waddlebot_payload function from the waddle_helpers objects
    payload = waddle_helpers.validate_waddlebot_payload(request.body.read())

    
    
    channel_id = payload["channel_id"]
    account = payload["account"]
    command_str_list = payload['command_string']
    
    # Set the community name to the first element of the command_str_list.
    community_name = command_str_list[0]

    # Get the community
    community = db(db.communities.community_name == community_name).select().first()
    if not community:
        return dict(msg="Community does not exist.", error=True, status=400)

    # Get the routing record from the routing table by the community_id. If it doesnt exist, throw an error.
    routing = db(db.routing.community_id == community.id).select().first()
    if not routing:
        return dict(msg="Community does not exist in the routings table.")

    # Get the routing gateway by the channel_id and account.
    routing_gateway = waddle_helpers.get_routing_gateway(channel_id, account)

    # Remove the routing gateway from the routing record, if it exists.
    routing_gateway_ids = routing.routing_gateway_ids
    if not routing_gateway_ids:
        return dict(msg="No routing gateways in community.")
    
    print("Gateways for the current community: ", routing_gateway_ids)
    if routing_gateway.id in routing_gateway_ids:
        routing_gateway_ids.remove(routing_gateway.id)
    else:
        return dict(msg="Routing gateway does not exist in community.")
    
    routing.update_record(routing_gateway_ids=routing_gateway_ids)

    return dict(msg="Routing removed from community.")
    