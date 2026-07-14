Security
========

This document explains the possible security risks in the Mattermost charm and
best practices to avoid them. It revolves around the practices from the charm
side. For details regarding upstream Mattermost configuration and broader
security considerations, please refer to the
`official Mattermost documentation <https://docs.mattermost.com/about/security.html>`__.

Outdated software
-----------------

Outdated software components, such as the upstream Mattermost workload or charm
dependencies, can introduce exploitable security vulnerabilities.

Best practices
~~~~~~~~~~~~~~

-  Regularly `upgrade the charm <https://charmhub.io/mattermost-k8s>`__ revision to
   include the latest charm components. Updates include security fixes from
   dependencies and the workload, as charm dependencies are regularly updated.
-  Regularly update Juju to the latest version to include security fixes.
-  Deploy observability, such as the
   `Canonical Observability Stack <https://charmhub.io/topics/canonical-observability-stack>`__,
   to detect unusual behaviours. See `How to integrate with COS </how-to/integrate-with-cos.md>`__.

Loss of data
------------

The Mattermost database or uploaded files can be lost or corrupted for various
reasons, including hardware failure, accidental deletion, or software errors.

.. _best-practices-1:

Best practices
~~~~~~~~~~~~~~

-  Use S3 for file storage so that uploads are stored externally and can be
   recovered independently of the workload. See `Integrations </reference/integrations.md>`__.
-  Use a dedicated `Charmed PostgreSQL <https://charmhub.io/postgresql-k8s>`__ and
   regularly back up the database through the charm's
   `backup action <https://canonical-charmed-postgresql.readthedocs-hosted.com/14/how-to/back-up-and-restore/create-a-backup/>`__.
-  Enable S3 server-side encryption by setting the ``s3-server-side-encryption``
   configuration option to ``true`` (requires a Mattermost Enterprise licence and
   S3-side configuration).

Unencrypted traffic
-------------------

If Mattermost serves plain HTTP, the traffic between Mattermost and its clients
is unencrypted, risking eavesdropping and tampering.

.. _best-practices-2:

Best practices
~~~~~~~~~~~~~~

-  Integrate the Mattermost charm with an ingress controller that provides TLS
   termination, such as
   `Traefik <https://charmhub.io/traefik-k8s>`__. The ``go-framework`` extension used
   by this charm provides built-in ingress support.
-  Ensure the SMTP relay connection is encrypted. When configuring the
   `smtp-integrator <https://charmhub.io/smtp-integrator>`__, use a transport
   security mode that enforces TLS (such as ``starttls``).

Authentication and access control
---------------------------------

Weak or mis-configured authentication increases the risk of unauthorized access
to sensitive team communications.

.. _best-practices-3:

Best practices
~~~~~~~~~~~~~~

-  Integrate the charm with an ``OAuth`` identity provider (such as
   `Hydra <https://charmhub.io/hydra>`__) to enable OpenID Connect-based single
   sign-on (SSO). This centralises authentication and enforces organisational
   login policies.
-  Limit the use of the ``grant-admin-role`` action to only the users who strictly
   require administrative privileges.
-  Keep the ``enable-user-access-tokens`` configuration option disabled (``false``)
   unless your workflows explicitly require Personal Access Tokens. If enabled,
   regularly audit issued tokens.

Push notification privacy
-------------------------

Push notification payloads that include message content can leak confidential
information if the push notification service or the device is compromised.

.. _best-practices-4:

Best practices
~~~~~~~~~~~~~~

-  Keep the ``push-notifications-include-message-snippet`` configuration option
   set to ``false`` (the default). This ensures push payloads include only a
   message identifier, and the full content is fetched by the mobile client
   directly from the Mattermost server.
-  Only configure ``push-notification-server`` to point to a trusted push proxy
   (for example, the Mattermost Hosted Push Notification Service or a
   self-hosted push proxy).

Image proxy
-----------

Without an image proxy, Mattermost clients fetch remote images directly, which
can expose client IP addresses to external servers and allow loading of insecure
or malicious content.

.. _best-practices-5:

Best practices
~~~~~~~~~~~~~~

-  Enable the built-in local image proxy by setting the ``image-proxy-enabled``
   configuration option to ``true``. This routes all remote image requests through
   the Mattermost server, anonymizing client connections and blocking insecure
   content.
