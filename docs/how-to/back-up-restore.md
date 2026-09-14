---
myst:
  html_meta:
    "description lang=en": "Learn about the backup and restoration process for the Mattermost charm."
---

(how_to_back_up_restore)=

# How to back up and restore

Mattermost is a stateless web application, and all states, including the chat
history and login, are stored inside the PostgreSQL database.

Refer to the [PostgreSQL charm's backup and restore guide](https://canonical.com/data/postgresql/docs/latest/how-to/back-up-and-restore/)
to back up and restore data in Mattermost.
