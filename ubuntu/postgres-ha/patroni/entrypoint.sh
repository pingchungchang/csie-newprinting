#!/bin/bash
set -e

# Patroni.yml uses env vars via ${VAR} syntax — render them with Python
python3 -c "
import os, re, sys
tpl = open('/etc/patroni/patroni.yml').read()
result = re.sub(r'\\\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), m.group(0)), tpl)
open('/tmp/patroni.yml','w').write(result)
"

# Ensure data directory parent exists with correct ownership and permissions
mkdir -p /var/lib/postgresql/data/patroni
chown -R postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data/patroni

# Background task: fix data directory permissions after pg_basebackup
(
  while true; do
    sleep 2
    if [ -d /var/lib/postgresql/data/patroni ]; then
      chmod 700 /var/lib/postgresql/data/patroni 2>/dev/null || true
    fi
  done
) &

exec su -s /bin/bash postgres -c "patroni /tmp/patroni.yml"
