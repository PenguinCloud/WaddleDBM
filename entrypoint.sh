#!/bin/bash
ansible-playbook entrypoint.yml  -c local 
/usr/local/bin/py4web run apps -H 0.0.0.0 -P 8000