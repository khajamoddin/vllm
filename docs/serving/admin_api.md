# Admin Control Plane

vLLM provides an optional **Admin Control Plane** designed for production environments. This control plane exposes a set of operational endpoints for monitoring, health checks, and safe lifecycle management (e.g., draining traffic), separate from the main inference API.

## Overview

The Admin Control Plane is:
- **Disabled by default**: Use `--enable-admin-api` to enable it.
- **Secure by default**: Runs on a separate port (`8001`) and binds to `localhost`.
- **Production-ready**: Provides primitives for K8s probes, load balancer health checks, and operational scripting.

## Enabling the Admin API

To enable the admin server, start vLLM with the following flags:

```bash
vllm serve Facebook/opt-125m \
    --enable-admin-api \
    --admin-port 8001 \
    --admin-host localhost
```

### Configuration Options

| Flag | Default | Description |
|------|---------|-------------|
| `--enable-admin-api` | `False` | Enables the Admin API server. |
| `--admin-port` | `8001` | The port for the admin server. |
| `--admin-host` | `localhost` | The interface to bind to. Defaults to pure local loopback for security. |

## Security Considerations

The Admin API is designed with a **Network Isolation** security model. By running on a separate port, operators can use standard network policies (Firewalls, Security Groups, K8s NetworkPolicies) to expose the Inference API (port 8000) publicly while keeping the Admin API (port 8001) restricted to the internal network or the pod itself.

## Admin CLI

vLLM includes a built-in reference client for the admin API.

```bash
# Check health
vllm admin status

# List loaded models
vllm admin models

# View queue statistics
vllm admin queue

# Drain the server (pause new requests)
vllm admin drain
```

## API Reference

Base URL: `http://localhost:8001`

### Health Check
**GET** `/v1/admin/health`

Returns `200 OK` if the engine is running and healthy, `503 Service Unavailable` otherwise. Useful for Kubernetes Liveness/Readiness probes.

```json
{
  "status": "healthy"
}
```

### Show Models
**GET** `/v1/admin/models`

Lists the currently loaded models. same structure as the OpenAI `/v1/models` endpoint but served on the admin port.

### Queue Statistics
**GET** `/v1/admin/queue`

Returns current queue depth and server load metrics. Requires `--enable-server-load-tracking` to be active on the main server.

### Drain Server
**POST** `/v1/admin/drain`

Gracefully pauses the engine. It stops accepting new requests but processes in-flight requests until completion. Useful for pre-stop hooks in Kubernetes.

### Reload Model
**POST** `/v1/admin/reload_model`

*Experimental*: Triggers a model reload. Currently returns `501 Not Implemented` if the underlying engine does not support dynamic reloading.
