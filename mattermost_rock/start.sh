#!/bin/bash

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -e

export MM_SQLSETTINGS_DRIVERNAME=postgres
export MM_SQLSETTINGS_DATASOURCE="postgres://${POSTGRESQL_DB_CONNECT_STRING#postgresql://}"
export MM_CONFIG="$MM_SQLSETTINGS_DATASOURCE"
export MM_SERVICESETTINGS_LISTENADDRESS=:8080
export MM_SERVICESETTINGS_SITEURL="${APP_BASE_URL:-http://localhost:8080}"

# S3 file storage configuration
if [ -n "$S3_BUCKET" ]; then
    export MM_FILESETTINGS_DRIVERNAME=amazons3
    export MM_FILESETTINGS_AMAZONS3ACCESSKEYID="$S3_ACCESS_KEY"
    export MM_FILESETTINGS_AMAZONS3SECRETACCESSKEY="$S3_SECRET_KEY"
    export MM_FILESETTINGS_AMAZONS3BUCKET="$S3_BUCKET"
    export MM_FILESETTINGS_AMAZONS3REGION="$S3_REGION"
    export MM_FILESETTINGS_AMAZONS3PATHPREFIX="${S3_PATH#/}"

    # Strip protocol from endpoint and determine SSL
    if echo "$S3_ENDPOINT" | grep -q "^https://"; then
        export MM_FILESETTINGS_AMAZONS3ENDPOINT="${S3_ENDPOINT#https://}"
        export MM_FILESETTINGS_AMAZONS3SSL=true
    else
        export MM_FILESETTINGS_AMAZONS3ENDPOINT="${S3_ENDPOINT#http://}"
        export MM_FILESETTINGS_AMAZONS3SSL=false
    fi
fi

exec /app/bin/mattermost
