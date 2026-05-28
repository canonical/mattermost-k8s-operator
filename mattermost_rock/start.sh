#!/bin/bash

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -e

# Helper: convert boolean config values to Mattermost-style ("true"/"false").
# Handles both Python-style ("True"/"False") and lowercase ("true"/"false").
to_mm_bool() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        true) echo "true" ;;
        *) echo "false" ;;
    esac
}

# ---------------------------------------------------------------------------
# Core database and service settings
# ---------------------------------------------------------------------------
export MM_SQLSETTINGS_DRIVERNAME=postgres
export MM_SQLSETTINGS_DATASOURCE="postgres://${POSTGRESQL_DB_CONNECT_STRING#postgresql://}"
export MM_CONFIG="$MM_SQLSETTINGS_DATASOURCE"
export MM_SERVICESETTINGS_LISTENADDRESS=:8080
export MM_SERVICESETTINGS_SITEURL="${APP_BASE_URL:-http://localhost:8080}"

# ---------------------------------------------------------------------------
# Charm config options (exposed by paas-charm as APP_* env vars)
# ---------------------------------------------------------------------------

# Licence
if [ -n "$APP_LICENCE" ]; then
    printf '%s' "$APP_LICENCE" > /tmp/mattermost-licence.txt
    export MM_SERVICESETTINGS_LICENSEFILELOCATION=/tmp/mattermost-licence.txt
fi

# Logging
export MM_LOGSETTINGS_ENABLECONSOLE=true
export MM_LOGSETTINGS_ENABLEFILE=false
if [ "$(to_mm_bool "$APP_DEBUG")" = "true" ]; then
    export MM_LOGSETTINGS_CONSOLELEVEL=DEBUG
else
    export MM_LOGSETTINGS_CONSOLELEVEL=INFO
fi

# Image proxy
MM_IMAGEPROXYSETTINGS_ENABLE="$(to_mm_bool "$APP_IMAGE_PROXY_ENABLED")"
export MM_IMAGEPROXYSETTINGS_ENABLE
export MM_IMAGEPROXYSETTINGS_IMAGEPROXYTYPE=local

# Team settings
if [ -n "$APP_MAX_CHANNELS_PER_TEAM" ]; then
    export MM_TEAMSETTINGS_MAXCHANNELSPERTEAM="$APP_MAX_CHANNELS_PER_TEAM"
fi
if [ -n "$APP_MAX_USERS_PER_TEAM" ]; then
    export MM_TEAMSETTINGS_MAXUSERSPERTEAM="$APP_MAX_USERS_PER_TEAM"
fi
if [ -n "$APP_PRIMARY_TEAM" ]; then
    export MM_TEAMSETTINGS_EXPERIMENTALPRIMARYTEAM="$APP_PRIMARY_TEAM"
fi

# File size limit (config is in MB, Mattermost expects bytes)
if [ -n "$APP_MAX_FILE_SIZE" ]; then
    export MM_FILESETTINGS_MAXFILESIZE=$(( APP_MAX_FILE_SIZE * 1048576 ))
fi

# Push notifications
if [ -n "$APP_PUSH_NOTIFICATION_SERVER" ]; then
    export MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS=true
    export MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER="$APP_PUSH_NOTIFICATION_SERVER"
    if [ "$(to_mm_bool "$APP_PUSH_NOTIFICATIONS_INCLUDE_MESSAGE_SNIPPET")" = "true" ]; then
        export MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS=full
    else
        export MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS=id_loaded
    fi
fi

# Clustering
if [ "$(to_mm_bool "$APP_CLUSTERING")" = "true" ]; then
    # Derive a stable cluster name from the app's base URL hostname
    CLUSTER_NAME=$(echo "$APP_BASE_URL" | sed 's|https\?://||' | cut -d. -f1 | cut -d: -f1)
    export MM_CLUSTERSETTINGS_ENABLE=true
    export MM_CLUSTERSETTINGS_CLUSTERNAME="$CLUSTER_NAME"
    export MM_CLUSTERSETTINGS_USEIPADDRESS=true
fi

# S3 server-side encryption
if [ "$(to_mm_bool "$APP_S3_SERVER_SIDE_ENCRYPTION")" = "true" ]; then
    export MM_FILESETTINGS_AMAZONS3SSE=true
fi

# S3 trace logging (enabled when debug is on and S3 is active)
if [ "$(to_mm_bool "$APP_DEBUG")" = "true" ] && [ -n "$S3_BUCKET" ]; then
    export MM_FILESETTINGS_AMAZONS3TRACE=true
fi

# Individual feature toggles (formerly bundled as "use_canonical_defaults")
MM_SERVICESETTINGS_CLOSEUNUSEDDIRECTMESSAGES="$(to_mm_bool "$APP_CLOSE_UNUSED_DIRECT_MESSAGES")"
export MM_SERVICESETTINGS_CLOSEUNUSEDDIRECTMESSAGES
MM_SERVICESETTINGS_ENABLECUSTOMEMOJI="$(to_mm_bool "$APP_ENABLE_CUSTOM_EMOJI")"
export MM_SERVICESETTINGS_ENABLECUSTOMEMOJI
MM_SERVICESETTINGS_ENABLELINKPREVIEWS="$(to_mm_bool "$APP_ENABLE_LINK_PREVIEWS")"
export MM_SERVICESETTINGS_ENABLELINKPREVIEWS
MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS="$(to_mm_bool "$APP_ENABLE_USER_ACCESS_TOKENS")"
export MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS

# ---------------------------------------------------------------------------
# S3 file storage configuration (from s3 integration)
# ---------------------------------------------------------------------------
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

# SMTP email settings configuration (from smtp integration)
# ---------------------------------------------------------------------------
if [ -n "$SMTP_HOST" ]; then
    export MM_EMAILSETTINGS_SENDEMAILNOTIFICATIONS=true
    export MM_EMAILSETTINGS_SMTPSERVER="$SMTP_HOST"
    export MM_EMAILSETTINGS_SMTPPORT="${SMTP_PORT:-25}"

    if [ -n "$SMTP_USER" ]; then
        export MM_EMAILSETTINGS_SMTPUSERNAME="$SMTP_USER"
    fi
    if [ -n "$SMTP_PASSWORD" ]; then
        export MM_EMAILSETTINGS_SMTPPASSWORD="$SMTP_PASSWORD"
    fi

    # Map auth type: only "plain" enables SMTP auth
    if [ "$SMTP_AUTH_TYPE" = "plain" ]; then
        export MM_EMAILSETTINGS_ENABLESMTPAUTH=true
    else
        export MM_EMAILSETTINGS_ENABLESMTPAUTH=false
    fi

    # Map transport security to Mattermost connection security values
    case "$SMTP_TRANSPORT_SECURITY" in
        tls)
            export MM_EMAILSETTINGS_CONNECTIONSECURITY=TLS
            ;;
        starttls)
            export MM_EMAILSETTINGS_CONNECTIONSECURITY=STARTTLS
            ;;
        *)
            export MM_EMAILSETTINGS_CONNECTIONSECURITY=""
            ;;
    esac

    # Map skip_ssl_verify (paas-charm emits Python bool strings: "True"/"False")
    if [ "$SMTP_SKIP_SSL_VERIFY" = "True" ]; then
        export MM_EMAILSETTINGS_SKIPHOSTVERIFICATION=true
    else
        export MM_EMAILSETTINGS_SKIPHOSTVERIFICATION=false
    fi

    # Use domain for the sender/reply-to address if provided
    if [ -n "$SMTP_DOMAIN" ]; then
        export MM_EMAILSETTINGS_FEEDBACKEMAIL="noreply@${SMTP_DOMAIN}"
        export MM_EMAILSETTINGS_REPLYTOADDRESS="noreply@${SMTP_DOMAIN}"
    fi
fi

# OpenID Connect (OAuth) configuration
if [ -n "$APP_OAUTH_CLIENT_ID" ]; then
    export MM_OPENIDSETTINGS_ENABLE=true
    export MM_OPENIDSETTINGS_ID="$APP_OAUTH_CLIENT_ID"
    export MM_OPENIDSETTINGS_SECRET="$APP_OAUTH_CLIENT_SECRET"
    # Construct the OIDC discovery endpoint from the issuer URL
    export MM_OPENIDSETTINGS_DISCOVERYENDPOINT="${APP_OAUTH_API_BASE_URL}/.well-known/openid-configuration"
fi

exec /app/bin/mattermost
