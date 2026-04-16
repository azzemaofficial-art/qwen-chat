# Trading Advisor Pro v7.0 - Helm Chart

## Installation

```bash
# Add the repository
helm repo add trading-advisor-pro https://charts.tradingadvisorpro.com
helm repo update

# Install with default values
helm install tap trading-advisor-pro/tap --namespace tap-system --create-namespace

# Install with custom values
helm install tap trading-advisor-pro/tap \
  --namespace tap-system \
  --create-namespace \
  -f custom-values.yaml

# Install for production
helm install tap trading-advisor-pro/tap \
  --namespace tap-system \
  --create-namespace \
  --values values-production.yaml
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount.api` | Number of API replicas | 3 |
| `replicaCount.ml` | Number of ML replicas | 2 |
| `image.api.repository` | API image repository | trading-advisor-pro/api |
| `image.api.tag` | API image tag | v7.0 |
| `image.ml.repository` | ML image repository | trading-advisor-pro/ml |
| `image.ml.tag` | ML image tag | v7.0 |
| `resources.api.requests.memory` | API memory request | 512Mi |
| `resources.api.requests.cpu` | API CPU request | 250m |
| `resources.ml.requests.memory` | ML memory request | 4Gi |
| `resources.ml.requests.cpu` | ML CPU request | 1000m |
| `autoscaling.enabled` | Enable HPA | true |
| `autoscaling.minReplicas` | Minimum replicas | 3 |
| `autoscaling.maxReplicas` | Maximum replicas | 20 |
| `database.enabled` | Deploy PostgreSQL | true |
| `redis.enabled` | Deploy Redis | true |
| `ingress.enabled` | Enable Ingress | true |
| `monitoring.enabled` | Enable Prometheus/Grafana | true |

## Uninstall

```bash
helm uninstall tap --namespace tap-system
```

## Upgrade

```bash
helm upgrade tap trading-advisor-pro/tap \
  --namespace tap-system \
  -f custom-values.yaml
```
