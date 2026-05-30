FROM quay.io/coreos/etcd:v3.5.17 AS etcd-bin
FROM alpine:3.20
COPY --from=etcd-bin /usr/local/bin/etcd /usr/local/bin/etcd
COPY --from=etcd-bin /usr/local/bin/etcdctl /usr/local/bin/etcdctl
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
