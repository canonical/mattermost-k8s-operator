---
title: ADR-001 - removing custom Canonical themes patch from the rock
author: Doğay Kamar (dogay.kamar@canonical.com)
date: 2026/03/24
domain: architecture
replaced-by: 
---

# Removing custom Canonical themes patch from the rock

As part of the Mattermost charm refactoring, a Mattermost rock replaced
the old `Dockerfile` approach. The new rock does not include a web app patch that
adds custom Canonical themes to the Mattermost frontend client.

This way, the rock is more generic, and the web app does not need to be rebuilt.


## Context

In the old podspec Mattermost charm, the Mattermost image was created with a
`Dockerfile`, and it included a patch that adds custom Canonical themes to the 
Mattermost web app. This meant that a certain part of the `Dockerfile` was
dedicated to downloading Mattermost's web app files directly from its GitHub
repository, applying the patch to the files, rebuilding the web app, and adding the new
client to the existing Mattermost release. Subsequently, a `https-proxy-agent`
patch was also applied to throttle concurrent proxy sockets to avoid
overwhelming the proxy server in case `npm`
tries to open a large number of connections when installing dependencies, which
would be the case in our company environments.

This resulted in a significantly increased image build time, as the rest
of the image build involved only file operations because Mattermost releases are normally
pre-built. It also meant that, with the new rock approach, when users deploy the
Mattermost charm from Charmhub, it would come with this additional patch that is
irrelevant to anyone outside of Canonical. As a product, we want to
keep it as clean and generic as possible, and expose configuration
options where possible.

## Decision

The Canonical themes patch is removed from the new Mattermost rock. In addition,
the `https-proxy-agent` patch is also removed now that there is no need to 
rebuild the frontend. This results in a cleaner and more generic rock, and the
build time decreased significantly.

It is also worth noting that during the investigation of these patches, we found
out that the old `https-proxy-agent` patch is outdated, and `npm` has a native configuration option
to set the maximum number of sockets, which would be the better option if we 
kept the frontend patches. This can be considered in the future as the solution
if we need to rebuild the frontend for any reason. 

## Consequences

When the Mattermost charm is updated to the newer revision, the Canonical theme
will not exist, and the users using the theme will be forced to switch to one of
the standard themes. This might create an initial discomfort for those who are
used to the color of the Canonical themes. However, Mattermost allows 
customizing theme colors, and to compensate, we can show users how to
customize their Mattermost to use the old custom themes.

Additionally, a part of `rockcraft.yaml` responsible for rebuilding the webapp is
removed, making the file shorter and cleaner. This also results in quicker
rock-packing. 