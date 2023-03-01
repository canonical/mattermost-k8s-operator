FROM ubuntu:focal AS canonical_flavour_builder

# Avoid needing any input from package installs.
ENV DEBIAN_FRONTEND=noninteractive

ARG mattermost_version=7.8.0

# Update ca-certificates before running git clone to ensure certs are up to
# date.
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y --no-install-recommends install \
        ca-certificates && \
    update-ca-certificates && \
    apt-get -y --no-install-recommends install \
        git

# We need version 16+ of NodeJS for `make package` to succeed.
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y --no-install-recommends install \
        curl \
        make \
        && \
    curl -s https://deb.nodesource.com/setup_16.x | bash && \
    apt-get -y update && \
    apt-get -y --no-install-recommends install nodejs

# Patch the https-proxy-agent library used by npm to limit the open socket
# number connected to proxy server.
# Currently, npm will open an unlimited number of sockets to the http proxy.
# For a large project, socket numbers may be up to thousands, which can cause
# issues in the build process. This patch will limit the open sockets connected
# to the http proxy server down to 15. The number can be adjusted by the
# NPM_HTTPS_PROXY_AGENT_MAX_SOCKETS environment variable.
COPY files/canonical_flavour/https-proxy-agent.patch patch/https-proxy-agent.patch

RUN curl -sSL https://github.com/TooTallNate/node-https-proxy-agent/archive/refs/tags/5.0.1.tar.gz -o node-https-proxy-agent.tar.gz && \
    echo "1afed785d8d9deadac371824d6622aeabc7919ed6db3b3a6ad0033bd1105d2f4  node-https-proxy-agent.tar.gz" | shasum -c && \
    tar -xf node-https-proxy-agent.tar.gz && \
    cd node-https-proxy-agent-5.0.1 && \
    git apply /patch/https-proxy-agent.patch && \
    npm config set progress=false loglevel=info && \
    npm install && \
    npm run build && \
    rm -rf /usr/lib/node_modules/npm/node_modules/https-proxy-agent/ && \
    mv ./dist /usr/lib/node_modules/npm/node_modules/https-proxy-agent && \
    cd ..

COPY files/canonical_flavour/themes.patch patch/themes.patch

RUN git clone -b v${mattermost_version} https://github.com/mattermost/mattermost-webapp

RUN cd mattermost-webapp && \
    git apply /patch/themes.patch && \
    npm config set progress=false loglevel=info && \
    make dist

FROM ubuntu:focal

ARG edition=enterprise
ARG image_flavour=default
ARG mattermost_gid=2000
ARG mattermost_uid=2000
ARG mattermost_version=7.8.0

LABEL org.label-schema.version=${mattermost_version}
LABEL com.canonical.image-flavour=${image_flavour}
LABEL com.canonical.mattermost-edition=${edition}

# We use "set -o pipefail"
SHELL ["/bin/bash", "-c"]

# python3-yaml needed to run juju actions, xmlsec1 needed if UseNewSAMLLibrary is set to false (the default)
RUN apt-get -qy update && \
    apt-get -qy upgrade && \
    apt-get -qy install curl python3-yaml xmlsec1 && \
    rm -f /var/lib/apt/lists/*_*

RUN mkdir -p /mattermost/data /mattermost/plugins /mattermost/client/plugins && \
    set -o pipefail && \
    case $edition in \
    enterprise) \
        curl https://releases.mattermost.com/$mattermost_version/mattermost-$mattermost_version-linux-amd64.tar.gz | tar -xvz ; \
        ;; \
    team) \
        curl https://releases.mattermost.com/$mattermost_version/mattermost-team-$mattermost_version-linux-amd64.tar.gz | tar -xvz ; \
        ;; \
    *) \
        echo "E: Unknown edition ${edition}!  Cannot continue." >&2 ; \
	exit 1 ; \
        ;; \
    esac && \
    addgroup --gid ${mattermost_gid} mattermost && \
    adduser --no-create-home --disabled-password --gecos "" --uid ${mattermost_uid} --gid ${mattermost_gid} --home /mattermost mattermost

# Enable prepackaged plugin
RUN if [ "$image_flavour" = canonical ]; then \
        tar -C /mattermost/plugins -xvzf /mattermost/prepackaged_plugins/mattermost-plugin-autolink-v1.2.2-linux-amd64.tar.gz ; \
    fi

# Enable prepackaged plugin
RUN if [ "$image_flavour" = canonical ]; then \
        tar -C /mattermost/plugins -xvzf /mattermost/prepackaged_plugins/mattermost-plugin-github-v2.1.4-linux-amd64.tar.gz ; \
    fi

# Enable prepackaged plugin
RUN if [ "$image_flavour" = canonical ]; then \
        tar -C /mattermost/plugins -xvzf /mattermost/prepackaged_plugins/mattermost-plugin-gitlab-v1.6.0-linux-amd64.tar.gz ; \
    fi

# Download and enable third-party plugin
RUN if [ "$image_flavour" = canonical ]; then \
	cd /mattermost/plugins && \
	set -o pipefail && \
	curl -L https://github.com/matterpoll/matterpoll/releases/download/v1.4.0/com.github.matterpoll.matterpoll-1.4.0.tar.gz | tar -xvz ; \
    fi

# Download and enable third-party plugin
RUN if [ "$image_flavour" = canonical ]; then \
	cd /mattermost/plugins && \
	set -o pipefail && \
	curl -L https://github.com/moussetc/mattermost-plugin-giphy/releases/download/v2.1.1/com.github.moussetc.mattermost.plugin.giphy-2.1.1.tar.gz | tar -xvz ; \
    fi

# Download and enable third-party plugin
RUN if [ "$image_flavour" = canonical ]; then \
	cd /mattermost/plugins && \
	set -o pipefail && \
	curl -L https://github.com/scottleedavis/mattermost-plugin-remind/releases/download/v0.4.5/com.github.scottleedavis.mattermost-plugin-remind-0.4.5.tar.gz | tar -xvz ; \
    fi

# Canonical's custom webapp
COPY --from=canonical_flavour_builder /mattermost-webapp/dist/. /canonical_flavour_tmp/ 
RUN if [ "$image_flavour" = canonical ]; then \
	rm -rf /mattermost/client && \
	cp -r /canonical_flavour_tmp/. /mattermost/client ; \
    fi

RUN rm -rf /canonical_flavour_tmp

HEALTHCHECK CMD curl --fail http://localhost:8065 || exit 1

CMD ["/mattermost/bin/mattermost"]
WORKDIR /mattermost

# The default port
EXPOSE 8065

VOLUME ["/mattermost/data", "/mattermost/logs", "/mattermost/config", "/mattermost/plugins", "/mattermost/client/plugins"]
