############################################################
# Dockerfile for SQLDD toolkit
############################################################

FROM python:3.6.0
MAINTAINER Rick Keilty "rkeilty@gmail.com"

# These are the common things we need
RUN apt-get update && apt-get install -y --no-install-recommends \
        mysql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove \
    && rm -rf /tmp/*

ENV SQLDD_SRC "/sql-data-dependency"
RUN mkdir -p "$SQLDD_SRC"

COPY requirements.txt "$SQLDD_SRC"
RUN pip install -r "$SQLDD_SRC/requirements.txt"

COPY MANIFEST.in "$SQLDD_SRC"
COPY README.rst "$SQLDD_SRC"
COPY setup.py "$SQLDD_SRC"
COPY sql_data_dependency "$SQLDD_SRC/sql_data_dependency"

RUN pip install -e "$SQLDD_SRC"

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["sqldd"]
