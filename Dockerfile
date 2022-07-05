FROM ubuntu:focal AS canonical_flavour_builder

RUN apt-get -qy update && \
    apt-get -qy dist-upgrade && \
    apt-get -qy install curl make python3-yaml && \
    curl -s https://deb.nodesource.com/setup_16.x | bash && \
    apt-get install nodejs -y && \
    (echo "2" && cat) | apt-get install git -y && \
    curl -qL https://www.npmjs.com/install.sh | sh

ARG mattermost_version=6.6.0

COPY themes.patch patch/themes.patch

RUN git clone -b v${mattermost_version} https://github.com/mattermost/mattermost-webapp && \
	cd mattermost-webapp && \
    git apply /patch/themes.patch && \
    make package ;

FROM ubuntu:focal

ARG edition=enterprise
ARG image_flavour=default
ARG mattermost_gid=2000
ARG mattermost_uid=2000
ARG mattermost_version=6.6.0

LABEL org.label-schema.version=${mattermost_version}
LABEL com.canonical.image-flavour=${image_flavour}
LABEL com.canonical.mattermost-edition=${edition}

SHELL ["/bin/bash", "-c"]

RUN apt-get -qy update && \
    apt-get -qy install curl ; 

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
        tar -C /mattermost/plugins -xvzf /mattermost/prepackaged_plugins/mattermost-plugin-github-v2.0.1-linux-amd64.tar.gz ; \
    fi

# Enable prepackaged plugin
RUN if [ "$image_flavour" = canonical ]; then \
        tar -C /mattermost/plugins -xvzf /mattermost/prepackaged_plugins/mattermost-plugin-gitlab-v1.3.0-linux-amd64.tar.gz ; \
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
