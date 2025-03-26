FROM  ghcr.io/penguincloud/web2py-core:latest AS BUILD
LABEL company="Penguin Tech Group LLC"
LABEL org.opencontainers.image.authors="info@penguintech.group"
LABEL license="GNU AGPL3"

# GET THE FILES WHERE WE NEED THEM!
COPY . /opt/manager/WaddleDBM/
WORKDIR /opt/manager/WaddleDBM


# PUT YER ARGS in here
ARG APP_TITLE="WB-dbm" #Change this to actual title for Default

# Install dependancies
RUN apt-get update && apt-get install -y python3
RUN pip install -r requirements.txt

# BUILD IT!
RUN ansible-playbook entrypoint.yml -c local --tags "build,run"

# PUT YER ENVS in here
ENV MATTERBRIDGE_URL="http://host.docker.internal:4200/api/message"
ENV MODULE_ONBOARD_URL="http://host.docker.internal:8000/WaddleDBM/api/module_onboarding/onboard_form"
ENV DEFAULT_USER="waddlebot_user"
ENV DEFAULT_PASSWORD="SwgPi13TvM8r"
ENV DEFAULT_EMAIL="<insert email>"

WORKDIR /var/www/html/py4web/

# Switch to non-root user
USER waddlebot

# Entrypoint time (aka runtime)
ENTRYPOINT ["/bin/bash","/opt/manager/WaddleDBM/entrypoint.sh"]