#!/bin/bash
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

pip install pip --upgrade
pip install pyopenssl --upgrade
pip install localstack==1.4.0
docker pull localstack/localstack:1.4.0
ACTIVATE_PRO=0 \
  EDGE_BIND_HOST=0.0.0.0 \
  EDGE_PORT=4566 \
  IMAGE_NAME=localstack/localstack:1.4.0 \
  localstack start --docker -d # Start LocalStack in the background (binding to all host ip)
echo "Waiting for LocalStack startup..." # Wait 30 seconds for the LocalStack container
localstack wait -t 30 # to become ready before timing out 
echo "Startup complete"
