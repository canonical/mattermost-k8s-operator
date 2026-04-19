#!/bin/bash

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -e

export MM_SQLSETTINGS_DRIVERNAME=postgres
export MM_SQLSETTINGS_DATASOURCE="postgres://${POSTGRESQL_DB_CONNECT_STRING#postgresql://}"
export MM_CONFIG="$MM_SQLSETTINGS_DATASOURCE"
export MM_SERVICESETTINGS_LISTENADDRESS=:8080
export MM_SERVICESETTINGS_SITEURL="${APP_BASE_URL:-http://localhost:8080}"

exec /app/bin/mattermost
