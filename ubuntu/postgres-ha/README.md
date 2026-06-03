# PostgreSQL High Availability — Patroni + etcd + HAProxy

A production-grade HA setup for PostgreSQL across 3 machines with automatic failover, split-brain protection, and transparent connection routing.

## Architecture

```
Machine 1 (node1)          Machine 2 (node2)          Machine 3 (node3)
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  etcd member 1   │      │  etcd member 2   │      │  etcd member 3   │
│  Patroni + PG    │◄────►│  Patroni + PG    │◄────►│  Patroni + PG    │
│  HAProxy         │      │  HAProxy         │      │  HAProxy         │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        │                         │                         │
        └─────────── Apps connect to ANY HAProxy ───────────┘
                     port 5000 = primary (read/write)
                     port 5001 = replicas (read-only)
```

### Components

| Component | Role |
|-----------|------|
| **Patroni** | Manages PostgreSQL lifecycle: init, replication, failover, fencing |
| **etcd** (3-node) | Distributed consensus store — leader election & split-brain prevention |
| **HAProxy** | Routes connections: port 5000 to primary, port 5001 round-robin to replicas |

### Why This Is Better Than Basic Replication

| Feature | Old (master/slave) | New (Patroni HA) |
|---------|--------------------|-------------------|
| Automatic failover | No — manual intervention | Yes — Patroni promotes replica in seconds |
| Split-brain protection | None | etcd quorum (2/3 nodes must agree) |
| Connection routing | Hardcoded IPs | HAProxy auto-discovers via Patroni API |
| Replica lag guard | None | Configurable max lag before failover |
| pg_rewind support | No | Yes — rejoins old primary without full resync |
| Health monitoring | None | Patroni REST API + HAProxy health checks |

## File Structure

```
ha/
├── .env                     # All configuration (edit per machine)
├── deploy.sh                # One-command deploy script
├── teardown.sh              # Cleanup script
├── patroni/
│   ├── Dockerfile           # PostgreSQL + Patroni image
│   ├── patroni.yml          # Patroni config template (env var substitution)
│   └── entrypoint.sh        # Renders config and starts Patroni
├── etcd/
│   └── Dockerfile           # etcd image (config via env vars)
└── haproxy/
    ├── Dockerfile           # HAProxy image
    ├── haproxy.cfg          # HAProxy config template
    └── entrypoint.sh        # Renders config and starts HAProxy
```

## Setup

### Prerequisites

- Docker installed on all 3 machines
- Machines can reach each other on ports: 2379, 2380 (etcd), 5432 (pg), 8008 (patroni), 5000-5001 (haproxy)
- Firewall rules allow traffic between the 3 nodes

### 1. Configure

Edit `.env` on **each machine** — only these 2 values change per machine:

| Machine | `NODE_NAME` | `NODE_IP` |
|---------|-------------|-----------|
| Machine 1 | `node1` | `192.168.1.101` |
| Machine 2 | `node2` | `192.168.1.102` |
| Machine 3 | `node3` | `192.168.1.103` |

Also update `NODE1_IP`, `NODE2_IP`, `NODE3_IP` to match your actual IPs.

### 2. Deploy (run on each machine)

```bash
bash deploy.sh
```

This builds images and starts etcd, Patroni, and HAProxy containers.

Start **node1 first** (it will bootstrap the cluster), then node2 and node3 (they'll join as replicas).

### 3. Verify

Check cluster status from any node:

```bash
# Patroni cluster status
docker exec pg-ha-patroni patronictl -c /tmp/patroni.yml list

# Expected output:
# + Cluster: pg-ha-cluster --+---------+---------+----+-----------+
# | Member | Host            | Role    | State   | TL | Lag in MB |
# +--------+-----------------+---------+---------+----+-----------+
# | node1  | 192.168.1.101   | Leader  | running |  1 |           |
# | node2  | 192.168.1.102   | Replica | running |  1 |         0 |
# | node3  | 192.168.1.103   | Replica | running |  1 |         0 |
# +--------+-----------------+---------+---------+----+-----------+
```

Check HAProxy stats dashboard: `http://<any-node-ip>:7000`

Test connectivity:

```bash
# Write to primary (port 5000)
psql -h <any-node-ip> -p 5000 -U postgres -d mydb -c "CREATE TABLE test(id serial);"

# Read from replica (port 5001)
psql -h <any-node-ip> -p 5001 -U postgres -d mydb -c "SELECT * FROM test;"
```

## Failover

### Automatic Failover

Kill the primary node's Patroni container or shut down the machine:

```bash
docker rm -f pg-ha-patroni   # on the primary node
```

Within ~30 seconds, Patroni promotes a replica to primary. HAProxy reroutes traffic automatically. **Zero application changes needed.**

### Manual Failover

```bash
docker exec pg-ha-patroni patronictl -c /tmp/patroni.yml switchover
```

Follow the interactive prompts to choose the new primary.

### Verify After Failover

```bash
docker exec pg-ha-patroni patronictl -c /tmp/patroni.yml list
```

The old primary will rejoin as a replica automatically (via pg_rewind) when it comes back.

## Ports Reference

| Port | Service | Purpose |
|------|---------|---------|
| 2379 | etcd | Client API |
| 2380 | etcd | Peer communication |
| 5432 | PostgreSQL | Direct PG access (avoid in production) |
| 8008 | Patroni | REST API + health checks |
| **5000** | **HAProxy** | **Primary (read/write) — use this** |
| **5001** | **HAProxy** | **Replicas (read-only) — use this** |
| 7000 | HAProxy | Stats dashboard |

## Application Connection Strings

Point your application to **any node's HAProxy**:

```
# Read/write (primary)
postgresql://postgres:postgres_password@192.168.1.101:5000/mydb

# Read-only (replicas, load-balanced)
postgresql://postgres:postgres_password@192.168.1.101:5001/mydb
```

For maximum availability, use multiple HAProxy endpoints in your connection string or put a DNS round-robin / load balancer in front of them.

## Teardown

```bash
bash teardown.sh
```

## Tuning

Edit `patroni.yml` DCS settings to adjust failover behavior:

| Setting | Default | Description |
|---------|---------|-------------|
| `ttl` | 30s | Leader key TTL — how long before a missing leader is considered dead |
| `loop_wait` | 10s | How often Patroni checks cluster state |
| `retry_timeout` | 10s | Timeout for DCS and PostgreSQL operations |
| `maximum_lag_on_failover` | 1MB | Don't promote replicas lagging more than this |
| `synchronous_mode` | false | Set to `true` for zero-data-loss (at cost of write latency) |
