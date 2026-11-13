---
myst:
    html_meta:
        "description lang=en": "Learn how to turn on, configure, and turn off mobile push notifications for the Mattermost charm."
---

(how_to_manage_push_notifications)=

# How to manage push notifications

Mattermost sends push notifications to its iOS and Android mobile apps through a push
proxy service. The push proxy forwards each notification to the Apple Push Notification
service or Google's Firebase Cloud Messaging, which deliver it to the device.

The `mattermost-k8s` charm manages push notifications with two configuration options:

| Option | Default | Description |
|--------|---------|-------------|
| `push-notification-server` | `""` | The URL of the push proxy service. Setting a URL turns on push notifications. |
| `push-notifications-include-message-snippet` | `false` | Whether notifications include the message text. Has no effect unless `push-notification-server` is set. |

While `push-notification-server` is set, the charm passes both settings to Mattermost as
environment variables. These override the matching settings in the Mattermost System
Console, which become read-only. While `push-notification-server` is empty, the charm
doesn't manage push notifications, and Mattermost uses the settings saved in the System
Console. On a new deployment, push notifications are off.

The commands in this guide assume the application is named `mattermost-k8s`.

## Choose a push notification service

Mattermost provides a hosted push proxy service, and you can also run your own:

| Service | URL | When to use it |
|---------|-----|----------------|
| Hosted Push Notification Service (HPNS) | `https://global.push.mattermost.com` | Production deployments with a Mattermost Professional or Enterprise license. |
| Test Push Notification Service (TPNS) | `https://push-test.mattermost.com` | Testing and non-commercial deployments. Not recommended for production. |
| Your own push proxy | The URL of your push proxy | Deployments that use custom-built mobile apps. |

The global HPNS URL balances requests across the regional endpoints. To keep traffic in one
region, use `https://us.push.mattermost.com`, `https://eu.push.mattermost.com`, or
`https://ap.push.mattermost.com` instead. The legacy `https://push.mattermost.com` and
`https://hpns-de.mattermost.com` URLs are deprecated.

HPNS and TPNS only work with the Mattermost apps published in the Apple App Store and the
Google Play Store. If you build your own mobile apps, you must host your own push proxy. See
[Host your own push proxy service](https://docs.mattermost.com/deployment-guide/mobile/host-your-own-push-proxy-service)
in the Mattermost documentation.

The examples in this guide use the global HPNS URL. To use a different service, replace the
URL in the commands.

## Check the current configuration

Check whether the charm already manages push notifications:

```
juju config mattermost-k8s push-notification-server
```

An empty output means that the charm isn't managing push notifications.

## Check the connection to the push notification service

The Mattermost workload must be able to reach the push notification service. Check the
connection from the Mattermost container:

```
juju ssh --container app mattermost-k8s/0 curl -sS --max-time 10 https://global.push.mattermost.com/version
```

The output shows the version of the push proxy, similar to:

```text
{"hash":"20f2a04","version":"6.6.0"}
```

If the command fails or times out, allow outbound HTTPS traffic from the Kubernetes
cluster to the push notification service before you continue.

## Turn on push notifications

Set the URL of the push notification service:

```
juju config mattermost-k8s push-notification-server=https://global.push.mattermost.com
```

The charm restarts Mattermost with the new settings. Wait for the application to become
active:

```
juju wait-for application mattermost-k8s
```

To check the settings in Mattermost, log in as a system administrator and go to
**System Console** > **Environment** > **Push Notification Server**. The settings
show the push notification server that you configured and can't be changed in the
System Console.

To test delivery, log in to the Mattermost mobile app, and ask another user to send you a
direct message. By default, the mobile app doesn't receive notifications while you're
actively using Mattermost in a web browser. If no notification arrives, see
[Mobile apps troubleshooting](https://docs.mattermost.com/deployment-guide/mobile/mobile-troubleshooting)
in the Mattermost documentation.

## Choose what push notifications contain

The `push-notifications-include-message-snippet` option controls whether the message text
leaves your Mattermost server inside the push notification:

* `false` (default): the charm configures ID-only push notifications. The notification
  contains only a message ID, and the mobile app fetches the message from your Mattermost
  server when the notification arrives. The mobile device must be able to reach your
  Mattermost server. ID-only push notifications require a Mattermost Entry, Enterprise,
  or Enterprise Advanced license, which you can provide with the `licence` configuration
  option. Without one of these licenses, notifications contain the sender and channel
  names, but not the message text.
* `true`: notifications contain the message text. The text passes through the push
  proxy service and through Apple's or Google's notification service.

To include the message text in push notifications, run:

```
juju config mattermost-k8s push-notifications-include-message-snippet=true
```

To stop including the message text in push notifications, run:

```
juju config mattermost-k8s push-notifications-include-message-snippet=false
```

For the security implications of each choice, see {ref}`explanation_security`.

## Turn off push notifications

Reset both configuration options to their defaults:

```
juju config mattermost-k8s --reset push-notification-server,push-notifications-include-message-snippet
```

The charm stops managing push notifications, and Mattermost uses the settings saved in the
System Console again. If push notifications were never turned on in the System Console,
they are now off.

If push notifications are still on, go to **System Console** > **Environment** >
**Push Notification Server**, set **Enable Push Notifications** to
**Do not send push notifications**, and save.

## Learn more

* [Enable push notifications](https://docs.mattermost.com/administration-guide/configure/push-notification-server-configuration-settings)
  in the Mattermost documentation describes the push notification services and their
  license requirements.
* [Push notification contents](https://docs.mattermost.com/administration-guide/configure/site-configuration-settings#push-notification-contents)
  in the Mattermost documentation describes each type of notification content.
* {ref}`reference_metrics` lists the push notification metrics that Mattermost exposes.
