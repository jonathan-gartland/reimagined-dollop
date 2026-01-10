# Extend the official Apache Airflow image to add git and other dependencies
ARG AIRFLOW_IMAGE_NAME=apache/airflow:3.1.5
FROM ${AIRFLOW_IMAGE_NAME}

# Switch to root to install system packages
USER root

# Install git and other system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up git config globally (will be overridden by environment variables in tasks)
RUN git config --system --add safe.directory /catalog-beta

# Switch back to airflow user
USER airflow

# Install Python dependencies needed by the DAG
RUN pip install --no-cache-dir \
    psycopg2-binary \
    python-dotenv
