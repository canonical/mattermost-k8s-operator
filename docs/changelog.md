# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-06-03

- Added custom Prometheus alert rules.

## 2026-05-09

- Added the following configuration options:
  - `licence`: Mattermost Enterprise Edition licence.
  - `clustering`: Enable high-availability clustering. Requires Enterprise licence.
  - `debug`: Set log level to DEBUG and enable S3 trace logging.
  - `image-proxy-enabled`: Enable the built-in local image proxy.
  - `max-channels-per-team`: Max channels per team.
  - `max-users-per-team`: Max users per team.
  - `max-file-size`: Max file upload size in MB.
  - `primary-team`: Lock users to a primary team.
  - `push-notification-server`: Push notification server URL.
  - `push-notifications-include-message-snippet`: Include message content in push payloads.
  - `s3-server-side-encryption`: Enable S3 server-side encryption.
  - `close-unused-direct-messages`: Auto-close inactive direct messages.
  - `enable-custom-emoji`: Allow custom emoji.
  - `enable-link-previews`: Enable link previews in messages.
  - `enable-user-access-tokens`: Allow Personal Access Tokens.

## 2026-05-01

- Added `grant-admin-role` action to promote users to system administrators.

## 2026-04-30

- Added SMTP integration.

## 2026-04-23

- Added S3 integration.

## 2026-03-20

- Added the initial, 12-factor charm with `postgres` relation.
- Added the first ever Mattermost rock.

## 2026-02-11

- Cleaned out and re-initialized the charm from the platform engineering charm template.