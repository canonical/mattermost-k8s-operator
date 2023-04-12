#!/bin/bash

pip install pip --upgrade
pip install pyopenssl --upgrade
pip install --upgrade localstack # install LocalStack cli
docker pull localstack/localstack # Make sure to pull the latest version of the image
id
chmod 777 /var/lib/localstack
ACTIVATE_PRO=0 \
  EDGE_BIND_HOST=0.0.0.0 \
  EDGE_PORT=4566 \
  IMAGE_NAME=localstack/localstack:2.0.1 \
  DEBUG=1 \
  LOCALSTACK_VOLUME_DIR=~/.cache/localstack/volume \
  SERVICES=s3 \
  localstack start -d # Start LocalStack in the background (binding to all host ip)
echo "Waiting for LocalStack startup..." # Wait 30 seconds for the LocalStack container
localstack wait -t 30 # to become ready before timing out 
echo "Startup complete"
