FROM python:3.11-bullseye
LABEL org.opencontainers.image.authors="tlinton@pdx.edu"
LABEL org.opencontainers.image.source=https://github.com/PSU-OIT-ARC/oregoninvasiveshotline

# Install project dependencies
RUN apt update -y && apt install -y \
  build-essential \
  binutils libgdal-dev proj-bin

# Set build arguments
ARG APP_PYTHON=python3.11
ARG APP_ENV=/opt/venv
ARG APP_REQUIREMENTS=requirements.txt

ARG APP_USER=invasives
ARG APP_USER_ID=1000
ARG APP_GROUP=invasives
ARG APP_GROUP_ID=1000

# Export build arguments as environment variables
ENV APP_PYTHON=${APP_PYTHON}
ENV APP_ENV=${APP_ENV}

ENV APP_USER=${APP_USER}
ENV APP_USER_ID=${APP_USER_ID}
ENV APP_GROUP=${APP_GROUP}
ENV APP_GROUP_ID=${APP_GROUP_ID}

# Configure user
RUN groupadd -g ${APP_GROUP_ID} "${APP_GROUP}" || echo "Group already exists"
RUN useradd -m -g "${APP_GROUP}" -u ${APP_USER_ID} "${APP_USER}" || echo "User already exists"

# Prepare application-local path
RUN chown ${APP_USER}:${APP_GROUP} /opt

# Prepare virtual environment
COPY --chown=${APP_USER}:${APP_GROUP} /Pipfile /
COPY --chown=${APP_USER}:${APP_GROUP} /Pipfile.lock /

#
RUN pip install pipenv

# Configure python virtual environment
USER ${APP_USER}
WORKDIR /

RUN ${APP_PYTHON} -m venv ${APP_ENV}
RUN PIPENV_CUSTOM_VENV_NAME=${APP_ENV} pipenv sync
# RUN PIPENV_CUSTOM_VENV_NAME=${APP_ENV} pipenv check
RUN ${APP_ENV}/bin/pip cache purge

# Install container entrypoint
WORKDIR /app
COPY /docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
