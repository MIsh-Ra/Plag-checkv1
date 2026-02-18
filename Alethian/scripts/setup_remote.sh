#!/bin/bash

# Configuration for Alethian Remote Development
HOST="alethian-dev"
HOSTNAME="172.22.2.151"
USER="23uec552"

# Check if entry already exists
if grep -q "$HOST" ~/.ssh/config; then
    echo "Host $HOST already exists in ~/.ssh/config"
else
    echo "Adding $HOST to ~/.ssh/config..."
    mkdir -p ~/.ssh
    touch ~/.ssh/config
    echo -e "\nHost $HOST\n    HostName $HOSTNAME\n    User $USER" >> ~/.ssh/config
    echo "Done! You can now connect to 'Host: $HOST' in VS Code."
fi
