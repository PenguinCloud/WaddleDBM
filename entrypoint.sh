#!/bin/bash
ansible-playbook entrypoint.yml  -c local 
echo "Sleeping awaiting action!"
sleep infinity