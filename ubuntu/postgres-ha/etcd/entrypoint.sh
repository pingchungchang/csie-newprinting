#!/bin/sh
if [ -d "/etcd-data/member" ]; then
  CLUSTER_STATE="existing"
else
  CLUSTER_STATE="new"
fi

unset ETCD_INITIAL_CLUSTER ETCD_CLIENT_PORT ETCD_PEER_PORT

exec etcd \
  --name=${NODE_NAME} \
  --data-dir=/etcd-data \
  --listen-client-urls=http://0.0.0.0:${ETCD_CLIENT_PORT} \
  --advertise-client-urls=http://${NODE_IP}:${ETCD_CLIENT_PORT} \
  --listen-peer-urls=http://0.0.0.0:${ETCD_PEER_PORT} \
  --initial-advertise-peer-urls=http://${NODE_IP}:${ETCD_PEER_PORT} \
  --initial-cluster=${ETCD_INITIAL_CLUSTER} \
  --initial-cluster-token=pg-ha-etcd-cluster \
  --initial-cluster-state=${CLUSTER_STATE} \
  --enable-v2=true
