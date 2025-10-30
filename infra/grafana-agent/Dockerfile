FROM grafana/agent:latest

COPY agent.yaml /etc/agent.yaml

ENTRYPOINT ["/usr/bin/grafana-agent"]
CMD ["--config.file=/etc/agent.yaml"]
