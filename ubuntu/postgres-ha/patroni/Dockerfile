ARG PG_VERSION=17
FROM postgres:${PG_VERSION}

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Patroni in a venv to avoid PEP 668 issues
RUN python3 -m venv /opt/patroni && \
    /opt/patroni/bin/pip install --no-cache-dir \
    patroni[etcd] \
    psycopg2-binary

ENV PATH="/opt/patroni/bin:${PATH}"

COPY patroni.yml /etc/patroni/patroni.yml
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY post_init.sh /usr/local/bin/post_init.sh
COPY init.sql /docker-entrypoint-initdb.d/init.sql
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/post_init.sh

ENTRYPOINT ["entrypoint.sh"]
