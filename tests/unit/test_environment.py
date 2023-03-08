# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import os
from unittest import mock

import pytest

import environment


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, ["mattermost_image_path"]),
        ({"mattermost_image_path": "placeholder"}, []),
        ({"mattermost_image_path": "placeholder", "clustering": "placeholder"}, ["licence"]),
        (
            {"mattermost_image_username": "placeholder"},
            ["mattermost_image_password", "mattermost_image_path"],
        ),
        ({"mattermost_image_path": "placeholder", "sso": "true"}, ["licence", "site_url"]),
    ],
)
def test_missing_config_settings(config, expected):
    """Test output of missing_config_settings function."""
    assert environment.missing_config_settings(config) == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, ()),
        (
            {
                "smtp_host": "placeholder",
                "smtp_connection_security": "placeholder",
                "smtp_from_address": "placeholder",
                "smtp_reply_to_address": "placeholder",
                "smtp_password": "placeholder",
                "smtp_user": "placeholder",
                "smtp_port": "placeholder",
            },
            (
                ("MM_EMAILSETTINGS_CONNECTIONSECURITY", "placeholder"),
                ("MM_EMAILSETTINGS_ENABLESMTPAUTH", "true"),
                ("MM_EMAILSETTINGS_FEEDBACKEMAIL", "placeholder"),
                ("MM_EMAILSETTINGS_REPLYTOADDRESS", "placeholder"),
                ("MM_EMAILSETTINGS_SMTPPASSWORD", "placeholder"),
                ("MM_EMAILSETTINGS_SMTPPORT", "placeholder"),
                ("MM_EMAILSETTINGS_SMTPSERVER", "placeholder"),
                ("MM_EMAILSETTINGS_SMTPUSERNAME", "placeholder"),
            ),
        ),
    ],
)
def test_env_for_smtp(config, expected):
    """Test output of env_for_smtp function."""
    assert tuple(environment._env_for_smtp(config)) == expected


@pytest.mark.parametrize(
    "config, site_url, expected",
    [
        ({}, "", ()),
        (
            {
                "sso": "true",
                "licence": "placeholder",
                "site_url": "http://placeholder.test",
            },
            "http://placeholder.test",
            (
                ("MM_EMAILSETTINGS_ENABLESIGNINWITHEMAIL", "false"),
                ("MM_EMAILSETTINGS_ENABLESIGNINWITHUSERNAME", "false"),
                ("MM_EMAILSETTINGS_ENABLESIGNUPWITHEMAIL", "false"),
                ("MM_SAMLSETTINGS_ENABLE", "true"),
                ("MM_SAMLSETTINGS_IDPURL", "https://login.ubuntu.com/saml/"),
                ("MM_SAMLSETTINGS_VERIFY", "true"),
                ("MM_SAMLSETTINGS_ENCRYPT", "false"),
                ("MM_SAMLSETTINGS_IDPDESCRIPTORURL", "https://login.ubuntu.com"),
                ("MM_SAMLSETTINGS_SERVICEPROVIDERIDENTIFIER", "https://login.ubuntu.com"),
                ("MM_SAMLSETTINGS_IDPMETADATAURL", "https://login.ubuntu.com/+saml/metadata"),
                (
                    "MM_SAMLSETTINGS_ASSERTIONCONSUMERSERVICEURL",
                    "https://placeholder.test/login/sso/saml",
                ),
                ("MM_SAMLSETTINGS_LOGINBUTTONTEXT", "Ubuntu SSO"),
                ("MM_SAMLSETTINGS_EMAILATTRIBUTE", "email"),
                ("MM_SAMLSETTINGS_USERNAMEATTRIBUTE", "username"),
                ("MM_SAMLSETTINGS_IDATTRIBUTE", "openid"),
                ("MM_SAMLSETTINGS_FIRSTNAMEATTRIBUTE", "fullname"),
                ("MM_SAMLSETTINGS_LASTNAMEATTRIBUTE", ""),
                ("MM_SAMLSETTINGS_IDPCERTIFICATEFILE", "saml-idp.crt"),
                ("MM_EXPERIMENTALSETTINGS_USENEWSAMLLIBRARY", "false"),
            ),
        ),
    ],
)
def test_env_for_sso(config, site_url, expected):
    """Test output of env_for_sso function."""
    assert tuple(environment._env_for_sso(config, site_url)) == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, ()),
        (
            {
                "push_notification_server": "placeholder",
                "push_notifications_include_message_snippet": "placeholder",
            },
            (
                ("MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS", "true"),
                ("MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS", "full"),
                ("MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER", "placeholder"),
            ),
        ),
    ],
)
def test_env_for_push(config, expected):
    """Test output of env_for_push function."""
    assert tuple(environment._env_for_push(config)) == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, ()),
        (
            {
                "performance_monitoring_enabled": "placeholder",
            },
            (
                ("MM_METRICSSETTINGS_ENABLE", "true"),
                ("MM_METRICSSETTINGS_LISTENADDRESS", ":8067"),
            ),
        ),
    ],
)
def test_env_for_performance_monitoring(config, expected):
    """Test output of env_for_performance_monitoring function."""
    assert tuple(environment._env_for_performance_monitoring(config)) == expected


@pytest.mark.parametrize(
    "config, app_name, expected",
    [
        (
            {},
            "placeholder",
            (),
        ),
        (
            {
                "clustering": "true",
            },
            "placeholder",
            (
                ("MM_CLUSTERSETTINGS_ENABLE", "true"),
                ("MM_CLUSTERSETTINGS_CLUSTERNAME", "placeholder-placeholder"),
                ("MM_CLUSTERSETTINGS_USEIPADDRESS", "true"),
            ),
        ),
    ],
)
@mock.patch.dict(os.environ, {"JUJU_MODEL_UUID": "placeholder"}, clear=True)
def test_env_for_clustering(config, app_name, expected):
    """Test output of env_for_clustering function."""
    assert tuple(environment._env_for_clustering(config, app_name)) == expected
