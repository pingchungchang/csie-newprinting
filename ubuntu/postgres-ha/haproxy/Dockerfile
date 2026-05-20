FROM haproxy:2.9

COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg.template
COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
