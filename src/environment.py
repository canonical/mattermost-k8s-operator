"""Generate container app environment based on charm configuration."""
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import os
from urllib.parse import urlparse

# Mattermost's default port, and what we expect the image to use
CONTAINER_PORT = 8065
# Default port, enforced via envConfig to prevent operator error
METRICS_PORT = 8067
REQUIRED_S3_SETTINGS = ("s3_bucket", "s3_region", "s3_access_key_id", "s3_secret_access_key")
REQUIRED_SETTINGS = ("mattermost_image_path",)
REQUIRED_SSO_SETTINGS = ("license", "site_url")
SAML_IDP_CRT = "saml-idp.crt"

CANONICAL_DEFAULTS = (
    # If this is off, users can't turn it on themselves.
    ("MM_SERVICESETTINGS_CLOSEUNUSEDDIRECTMESSAGES", "true"),
    # This allows Matterhorn to use emoji and react to messages.
    ("MM_SERVICESETTINGS_ENABLECUSTOMEMOJI", "true"),
    # If this is off, users can't turn it on themselves.
    ("MM_SERVICESETTINGS_ENABLELINKPREVIEWS", "true"),
    # Matterhorn recommends the use of Personal Access Tokens.
    ("MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS", "true"),
    # We'll use one large team.  Create and invite are
    # disabled in the System Scheme, found in the Permissions
    # section of the System Console.
    ("MM_TEAMSETTINGS_MAXUSERSPERTEAM", "1000"),
)


def _env_for_clustering(config: dict, app_name: str) -> tuple:
    """Return clustering settings, varying the cluster name on the application name.

    This is done so that blue/green deployments in the same model won't talk to each other.

    Args:
        config: dict of the charm's configuration
        app_name: name of the charm's app

    Returns:
        dict of clustering settings, varying the cluster name on the application name.
    """
    if not config.get("clustering"):
        return ()
    return (
        ("MM_CLUSTERSETTINGS_ENABLE", "true"),
        # https://juju.is/docs/sdk/charm-environment-variables
        ("MM_CLUSTERSETTINGS_CLUSTERNAME", f"{app_name}-{os.environ.get('JUJU_MODEL_UUID')}"),
        ("MM_CLUSTERSETTINGS_USEIPADDRESS", "true"),
    )


def _env_for_performance_monitoring(config: dict) -> tuple:
    """Return settings for the Prometheus exporter.

    Args:
        config: dict of the charm's configuration

    Returns:
        dict of settings for the Prometheus exporter.
    """
    if not config.get("performance_monitoring_enabled"):
        return ()

    return (
        (
            "MM_METRICSSETTINGS_ENABLE",
            "true" if config.get("performance_monitoring_enabled") else "false",
        ),
        ("MM_METRICSSETTINGS_LISTENADDRESS", f":{METRICS_PORT}"),
    )


def _env_for_push(config: dict) -> tuple:
    """Return settings for Mattermost HPNS (hosted push notification service).

    Args:
        config: dict of the charm's configuration

    Returns:
        dict of settings for Mattermost HPNS (hosted push notification service).
    """
    if not config.get("push_notification_server"):
        return ()

    contents = "full" if config.get("push_notifications_include_message_snippet") else "id_loaded"

    return (
        ("MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS", "true"),
        ("MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS", contents),
        ("MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER", config.get("push_notification_server")),
    )


def _env_for_sso(config: dict, site_url: str) -> tuple:
    """Return settings to use login.ubuntu.com via SAML for single sign-on.

    SAML_IDP_CRT must be generated and installed manually by a human (see README.md).

    Args:
        config: dict of the charm's configuration
        site_url: public facing URL of mattermost

    Returns:
        dict of settings to use login.ubuntu.com via SAML for single sign-on.
    """
    if not config.get("sso") or any(not config.get(setting) for setting in REQUIRED_SSO_SETTINGS):
        return ()
    site_hostname = urlparse(site_url).hostname
    use_experimental_saml_library = (
        "true" if config.get("use_experimental_saml_library") else "false"
    )

    return (
        ("MM_EMAILSETTINGS_ENABLESIGNINWITHEMAIL", "false"),
        ("MM_EMAILSETTINGS_ENABLESIGNINWITHUSERNAME", "false"),
        ("MM_EMAILSETTINGS_ENABLESIGNUPWITHEMAIL", "false"),
        ("MM_SAMLSETTINGS_ENABLE", "true"),
        ("MM_SAMLSETTINGS_IDPURL", "https://login.ubuntu.com/saml/"),
        ("MM_SAMLSETTINGS_VERIFY", "true"),
        ("MM_SAMLSETTINGS_ENCRYPT", "false"),  # per POC
        ("MM_SAMLSETTINGS_IDPDESCRIPTORURL", "https://login.ubuntu.com"),
        ("MM_SAMLSETTINGS_SERVICEPROVIDERIDENTIFIER", "https://login.ubuntu.com"),
        ("MM_SAMLSETTINGS_IDPMETADATAURL", "https://login.ubuntu.com/+saml/metadata"),
        ("MM_SAMLSETTINGS_ASSERTIONCONSUMERSERVICEURL", f"https://{site_hostname}/login/sso/saml"),
        ("MM_SAMLSETTINGS_LOGINBUTTONTEXT", "Ubuntu SSO"),
        ("MM_SAMLSETTINGS_EMAILATTRIBUTE", "email"),
        ("MM_SAMLSETTINGS_USERNAMEATTRIBUTE", "username"),
        ("MM_SAMLSETTINGS_IDATTRIBUTE", "openid"),
        ("MM_SAMLSETTINGS_FIRSTNAMEATTRIBUTE", "fullname"),
        ("MM_SAMLSETTINGS_LASTNAMEATTRIBUTE", ""),
        ("MM_SAMLSETTINGS_IDPCERTIFICATEFILE", SAML_IDP_CRT),
        # If not set, we have to install xmlsec1, and Mattermost forks on every login(!).
        ("MM_EXPERIMENTALSETTINGS_USENEWSAMLLIBRARY", use_experimental_saml_library),
    )


def _env_for_smtp(config: dict) -> tuple:
    """Return settings for an outgoing SMTP relay.

    Args:
        config: dict of the charm's configuration

    Returns:
        dict of settings for an outgoing SMTP relay.
    """
    if any(
        (
            setting not in config
            for setting in (
                "smtp_host",
                "smtp_connection_security",
                "smtp_from_address",
                "smtp_reply_to_address",
                "smtp_password",
                "smtp_user",
                "smtp_port",
            )
        )
    ):
        return ()

    if not config["smtp_host"]:
        return ()

    enable_smtp_auth = "false"
    if config["smtp_user"] and config["smtp_password"]:
        enable_smtp_auth = "true"

    # https://github.com/mattermost/mattermost-server/blob/master/model/config.go#L1532
    return (
        ("MM_EMAILSETTINGS_CONNECTIONSECURITY", config["smtp_connection_security"]),
        ("MM_EMAILSETTINGS_ENABLESMTPAUTH", enable_smtp_auth),
        ("MM_EMAILSETTINGS_FEEDBACKEMAIL", config["smtp_from_address"]),
        ("MM_EMAILSETTINGS_REPLYTOADDRESS", config["smtp_reply_to_address"]),
        ("MM_EMAILSETTINGS_SMTPPASSWORD", config["smtp_password"]),
        ("MM_EMAILSETTINGS_SMTPPORT", config["smtp_port"]),
        ("MM_EMAILSETTINGS_SMTPSERVER", config["smtp_host"]),
        ("MM_EMAILSETTINGS_SMTPUSERNAME", config["smtp_user"]),
    )


def missing_config_settings(config: dict) -> list:
    """Return a list of settings required to satisfy configuration dependencies.

    Args:
        config: dict of the charm's configuration

    Returns:
        a list of settings required to satisfy configuration dependencies.
    """
    missing = [setting for setting in REQUIRED_SETTINGS if not config.get(setting)]

    if config.get("clustering") and not config.get("license"):
        missing.append("license")

    if config.get("mattermost_image_username") and not config.get("mattermost_image_password"):
        missing.append("mattermost_image_password")

    if config.get("performance_monitoring_enabled") and not config.get("license"):
        missing.append("license")

    if config.get("s3_enabled"):
        missing += [setting for setting in REQUIRED_S3_SETTINGS if not config.get(setting)]

    if config.get("s3_server_side_encryption") and not config.get("license"):
        missing.append("license")

    if config.get("sso") == "true":
        missing += [setting for setting in REQUIRED_SSO_SETTINGS if not config.get(setting)]

    return sorted(missing)


def generate(config: dict, app_name: str, site_url: str, db_uri: str) -> dict:
    """Generate container app environment based on charm configuration.

    Args:
        config: dict of the charm's configuration
        app_name: name of the app
        site_url: public facing URL of mattermost
        db_uri: URI of the psql database

    Returns:
        dict of container app environment.
    """
    # https://github.com/mattermost/mattermost-server/pull/14666
    db_uri = db_uri.replace("postgresql://", "postgres://")
    env = {
        "MATTERMOST_HTTPD_LISTEN_PORT": str(CONTAINER_PORT),
        "MM_CONFIG": db_uri,
        "MM_SQLSETTINGS_DATASOURCE": db_uri,
        # image proxy
        "MM_IMAGEPROXYSETTINGS_ENABLE": "true" if config["image_proxy_enabled"] else "false",
        "MM_IMAGEPROXYSETTINGS_IMAGEPROXYTYPE": "local",
        # logging
        "MM_LOGSETTINGS_CONSOLELEVEL": "DEBUG" if config["debug"] else "INFO",
        "MM_LOGSETTINGS_ENABLECONSOLE": "true",
        "MM_LOGSETTINGS_ENABLEFILE": "false",
        "MM_TEAMSETTINGS_MAXCHANNELSPERTEAM": config["max_channels_per_team"],
        "MM_TEAMSETTINGS_MAXUSERSPERTEAM": config["max_users_per_team"],
        "MM_SERVICESETTINGS_SITEURL": site_url,
    }

    if config["primary_team"]:
        env["MM_TEAMSETTINGS_EXPERIMENTALPRIMARYTEAM"] = config["primary_team"]

    if config["outbound_proxy"]:
        env["HTTP_PROXY"] = config["outbound_proxy"]
        env["HTTPS_PROXY"] = config["outbound_proxy"]
        if config["outbound_proxy_exceptions"]:
            env["NO_PROXY"] = config["outbound_proxy_exceptions"]

    if config["s3_enabled"]:
        env.update(
            {
                "MM_FILESETTINGS_DRIVERNAME": "amazons3",
                "MM_FILESETTINGS_MAXFILESIZE": config["max_file_size"] * 1048576,  # LP:1881227
                "MM_FILESETTINGS_AMAZONS3SSL": "true",  # defaults to true; belt and braces
                "MM_FILESETTINGS_AMAZONS3ENDPOINT": config["s3_endpoint"],
                "MM_FILESETTINGS_AMAZONS3BUCKET": config["s3_bucket"],
                "MM_FILESETTINGS_AMAZONS3REGION": config["s3_region"],
                "MM_FILESETTINGS_AMAZONS3ACCESSKEYID": config["s3_access_key_id"],
                "MM_FILESETTINGS_AMAZONS3SECRETACCESSKEY": config["s3_secret_access_key"],
                "MM_FILESETTINGS_AMAZONS3SSE": "true"
                if config["s3_server_side_encryption"]
                else "false",
                "MM_FILESETTINGS_AMAZONS3TRACE": "true" if config["debug"] else "false",
            }
        )

    if config["use_canonical_defaults"]:
        env.update(CANONICAL_DEFAULTS)

    env.update(_env_for_clustering(config, app_name))
    env.update(_env_for_performance_monitoring(config))
    env.update(_env_for_push(config))
    env.update(_env_for_sso(config, site_url))
    env.update(_env_for_smtp(config))

    # make sure to convert all values to str
    env = {env_name: str(env_value) for env_name, env_value in env.items()}

    return env
