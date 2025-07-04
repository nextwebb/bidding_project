# AdTech Bidding Engine Helm Chart

A production-ready Helm chart for deploying the AdTech Bidding Engine on Amazon EKS (Elastic Kubernetes Service).

## Overview

This chart deploys:
- **Web Application**: Django REST API with autoscaling
- **Worker Processes**: Huey async task workers
- **Competitor Monitor**: TypeScript microservice for price monitoring
- **PostgreSQL**: Primary database (using Bitnami chart)
- **Redis**: Message queue and caching (using Bitnami chart)

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Amazon EKS cluster
- AWS Load Balancer Controller (for ALB ingress)

## Installation

### Quick Start

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install the chart
helm install adtech-bidding ./chart
```

### Production Installation

```bash
# Create namespace
kubectl create namespace adtech

# Install with production values
helm install adtech-bidding ./chart \
  --namespace adtech \
  --values chart/values-production.yaml \
  --set image.tag=v1.2.3 \
  --set ingress.hosts[0].host=api.adtech.company.com
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of web application replicas | `2` |
| `image.repository` | Container image repository | `adtech/bidding-engine` |
| `image.tag` | Container image tag | `latest` |
| `service.type` | Kubernetes service type | `LoadBalancer` |
| `ingress.enabled` | Enable ingress controller | `true` |
| `autoscaling.enabled` | Enable horizontal pod autoscaling | `true` |
| `postgresql.enabled` | Enable PostgreSQL dependency | `true` |
| `redis.enabled` | Enable Redis dependency | `true` |

### Environment Configuration

```yaml
env:
  DEBUG: "0"
  LOG_LEVEL: "INFO"
  DATABASE_URL: "postgres://..."
  REDIS_URL: "redis://..."
```

### Resource Limits

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

## Components

### Web Application
- **Replicas**: 2-10 (autoscaling)
- **Service**: LoadBalancer on port 80
- **Health Checks**: Liveness and readiness probes
- **Resources**: CPU and memory limits defined

### Worker Processes
- **Replicas**: 2 (configurable)
- **Function**: Processes Huey async tasks
- **Resources**: Optimized for background processing

### Competitor Monitor
- **Replicas**: 1
- **Function**: Fetches competitor prices from external APIs
- **Health Checks**: Custom health endpoint

### Database (PostgreSQL)
- **Storage**: Persistent volume with GP3
- **Resources**: Production-ready resource allocation
- **Backup**: Configurable backup jobs

### Cache/Queue (Redis)
- **Mode**: Master-only (suitable for development)
- **Persistence**: Enabled with persistent volumes
- **Resources**: Memory-optimized configuration

## Ingress Configuration

The chart supports AWS Application Load Balancer (ALB) ingress:

```yaml
ingress:
  enabled: true
  className: "alb"
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
```

## Security

### Pod Security Context
```yaml
podSecurityContext:
  fsGroup: 2000

securityContext:
  capabilities:
    drop: [ALL]
  readOnlyRootFilesystem: false
  runAsNonRoot: true
  runAsUser: 1000
```

### Service Account
- Dedicated service account created
- RBAC permissions as needed
- Can be configured with AWS IAM roles (IRSA)

## Monitoring

### Health Checks
- **Liveness Probe**: `/health/` endpoint
- **Readiness Probe**: `/health/` endpoint
- **Startup Probe**: Configurable delay

### Metrics (Optional)
```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true  # For Prometheus
  prometheusRule:
    enabled: true  # Custom alerting rules
```

## Deployment Examples

### Development
```bash
helm install adtech-dev ./chart \
  --set env.DEBUG=1 \
  --set replicaCount=1 \
  --set autoscaling.enabled=false
```

### Staging
```bash
helm install adtech-staging ./chart \
  --namespace staging \
  --set image.tag=staging \
  --set ingress.hosts[0].host=staging-api.adtech.com
```

### Production
```bash
helm install adtech-prod ./chart \
  --namespace production \
  --set image.tag=v1.2.3 \
  --set replicaCount=3 \
  --set resources.limits.memory=1Gi \
  --set postgresql.primary.persistence.size=50Gi
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade adtech-bidding ./chart \
  --set image.tag=v1.3.0

# Upgrade with new values
helm upgrade adtech-bidding ./chart \
  --values chart/values-production.yaml
```

## Backup

Enable automatic database backups:

```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: "7"         # Keep 7 days
```

## Troubleshooting

### Common Issues

1. **Pod startup failures**: Check resource limits and health check timeouts
2. **Database connection**: Verify PostgreSQL service is running
3. **Redis connection**: Check Redis service and network policies

### Debug Commands

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=adtech-bidding-engine

# View logs
kubectl logs deployment/adtech-bidding-engine

# Check services
kubectl get svc -l app.kubernetes.io/name=adtech-bidding-engine

# Describe ingress
kubectl describe ingress adtech-bidding-engine
```

## Values Reference

See [values.yaml](values.yaml) for complete configuration options.

## Dependencies

This chart depends on:
- [Bitnami PostgreSQL](https://github.com/bitnami/charts/tree/master/bitnami/postgresql)
- [Bitnami Redis](https://github.com/bitnami/charts/tree/master/bitnami/redis)

## Contributing

1. Make changes to templates or values
2. Test with `helm template ./chart`
3. Validate with `helm lint ./chart`
4. Submit pull request
