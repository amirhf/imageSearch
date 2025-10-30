FROM grafana/agent:latest

COPY agent.yaml /etc/agent.yaml

# Cloud Run requires a listening HTTP server. Enable Agent's HTTP server on $PORT.
ENTRYPOINT ["/usr/bin/grafana-agent"]
CMD ["--config.file=/etc/agent.yaml", "--server.http.listen-address=0.0.0.0:${PORT:-8080}"]
