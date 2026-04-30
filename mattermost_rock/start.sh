#!/bin/bash

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

set -e

export MM_SQLSETTINGS_DRIVERNAME=postgres
export MM_SQLSETTINGS_DATASOURCE="postgres://${POSTGRESQL_DB_CONNECT_STRING#postgresql://}"
export MM_CONFIG="$MM_SQLSETTINGS_DATASOURCE"
export MM_SERVICESETTINGS_LISTENADDRESS=:8080

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

# SMTP email settings configuration
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

exec /app/bin/mattermost
