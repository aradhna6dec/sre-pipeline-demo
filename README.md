# Production-Ready SRE Pipeline Demo

**Senior Lead SRE Level Implementation**

A complete, production-grade CI/CD pipeline demonstrating 20+ years of SRE best practices with FastAPI, Docker, Kubernetes, and full observability.

---

## 🎯 Project Overview

This project demonstrates a **complete production-ready microservice** with enterprise-grade:
- ✅ **Application**: FastAPI with structured logging, metrics, health checks
- ✅ **Containerization**: Multi-stage Docker builds (distroless, rootless)
- ✅ **CI/CD**: GitHub Actions, Jenkins, GitOps (ArgoCD) - all three approaches
- ✅ **Kubernetes**: HPA, PDB, resource limits, security contexts
- ✅ **Observability**: Prometheus, Grafana, Loki, Jaeger (full stack)
- ✅ **Testing**: Unit, integration, load, chaos engineering
- ✅ **Security**: Vulnerability scanning, RBAC, network policies
- ✅ **Documentation**: Runbooks, troubleshooting guides, architecture docs

---

## 📊 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│  CI Pipeline │────▶│   Registry  │
│             │     │  (Actions/   │     │   (GHCR)    │
│             │     │   Jenkins)   │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   ArgoCD     │────▶│ Kubernetes  │
                    │   (GitOps)   │     │   Cluster   │
                    └──────────────┘     └─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────┐
                    │                           │                       │
                    ▼                           ▼                       ▼
            ┌──────────────┐          ┌──────────────┐        ┌──────────────┐
            │  Prometheus  │          │     Loki     │        │    Jaeger    │
            │   (Metrics)  │          │    (Logs)    │        │   (Traces)   │
            └──────────────┘          └──────────────┘        └──────────────┘
                    │                           │                       │
                    └───────────────────────────┼───────────────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │   Grafana    │
                                        │ (Dashboards) │
                                        └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (for local development)
- kubectl (for Kubernetes)
- Python 3.11+ (for local development)
- Optional: Kubernetes cluster (minikube, kind, or cloud)

### Local Development (Docker Compose)

```bash
# 1. Clone repository
git clone <repo-url>
cd sre-pipeline-demo

# 2. Start full stack (app + observability)
docker-compose up -d

# 3. Access services
# - Application:  http://localhost:8000
# - API Docs:     http://localhost:8000/docs
# - Prometheus:   http://localhost:9090
# - Grafana:      http://localhost:3000 (admin/admin)
# - Jaeger:       http://localhost:16686

# 4. Test the API
curl http://localhost:8000/api/v1/items

# 5. Check metrics
curl http://localhost:8000/metrics

# 6. View logs in Loki
# Open Grafana → Explore → Select Loki → Query: {service="sre-demo-api"}
```

### Production Deployment (Kubernetes)

```bash
# 1. Apply Kubernetes manifests
kubectl create namespace production
kubectl apply -k k8s/overlays/prod/

# 2. Verify deployment
kubectl get pods -n production -l app=sre-demo-api
kubectl get svc -n production sre-demo-api

# 3. Check rollout status
kubectl rollout status deployment/sre-demo-api -n production

# 4. Access application
kubectl port-forward -n production svc/sre-demo-api 8000:80
```

---

## 🏗️ Project Structure

```
sre-pipeline-demo/
├── app/                          # Application code
│   ├── main.py                   # FastAPI application
│   ├── api/
│   │   └── routes.py            # API endpoints
│   ├── core/
│   │   ├── config.py            # Configuration management
│   │   ├── logging_config.py   # Structured logging
│   │   └── metrics.py           # Prometheus metrics
│   └── models/
│       └── schemas.py           # Pydantic models
│
├── docker/                       # Dockerfiles
│   ├── production/
│   │   └── Dockerfile           # Distroless, rootless (recommended)
│   ├── standard/
│   │   └── Dockerfile           # Security-hardened with debug tools
│   └── development/
│       └── Dockerfile           # Full tooling, hot reload
│
├── k8s/                          # Kubernetes manifests
│   ├── base/                     # Base resources
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── config.yaml
│   │   └── kustomization.yaml
│   └── overlays/                 # Environment-specific
│       ├── dev/
│       ├── staging/
│       └── prod/
│
├── ci-cd/                        # CI/CD pipelines
│   ├── github-actions/
│   │   └── ci-cd.yml            # GitHub Actions workflow
│   ├── jenkins/
│   │   └── Jenkinsfile          # Jenkins pipeline
│   └── argocd/
│       └── application.yaml     # ArgoCD GitOps config
│
├── observability/                # Observability stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   ├── alerts.yml
│   │   └── alertmanager.yml
│   ├── grafana/
│   │   ├── provisioning/
│   │   └── dashboards/
│   ├── loki/
│   │   ├── loki-config.yml
│   │   └── promtail-config.yml
│   └── jaeger/
│
├── tests/                        # Tests
│   ├── unit/
│   ├── integration/
│   ├── load/
│   └── chaos/
│
├── docs/                         # Documentation
│   ├── architecture/
│   ├── runbooks/
│   └── troubleshooting/
│       └── TROUBLESHOOTING.md
│
├── docker-compose.yml            # Local development stack
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🐳 Docker Build Strategies

### Approach 1: Production (Distroless + Rootless) ⭐ RECOMMENDED

**Use Case:** Production deployments where security is paramount

```bash
docker build -f docker/production/Dockerfile -t sre-demo-api:prod .
docker run -p 8000:8000 sre-demo-api:prod
```

**Characteristics:**
- ✅ Non-root user (UID 65532)
- ✅ Distroless base (~50MB)
- ✅ No shell, no package manager
- ✅ Minimal attack surface
- ❌ Cannot `docker exec` for debugging
- ❌ Harder to troubleshoot

### Approach 2: Standard (Security Hardened)

**Use Case:** Production where you need some debugging capability

```bash
docker build -f docker/standard/Dockerfile -t sre-demo-api:standard .
docker run -p 8000:8000 sre-demo-api:standard
```

**Characteristics:**
- ✅ Non-root user (UID 1001)
- ✅ Security updates applied
- ✅ Shell available for debugging
- ✅ Health checks included
- ⚠️ Larger image (~200MB)
- ⚠️ Slightly larger attack surface

### Approach 3: Development

**Use Case:** Local development with hot reload

```bash
docker build -f docker/development/Dockerfile -t sre-demo-api:dev .
docker run -p 8000:8000 -v $(pwd)/app:/app/app sre-demo-api:dev
```

**Characteristics:**
- ✅ Full Python image with tools
- ✅ Auto-reload on code changes
- ✅ Debugging tools installed
- ❌ Running as root (DO NOT use in production)
- ❌ Large image (~1GB)

### Comparison Table

| Feature | Production | Standard | Development |
|---------|------------|----------|-------------|
| **Image Size** | ~50MB | ~200MB | ~1GB |
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Debug Ease** | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Hot Reload** | ❌ | ❌ | ✅ |
| **Shell Access** | ❌ | ✅ | ✅ |
| **Root User** | ❌ | ❌ | ✅ (⚠️) |

---

## 🔄 CI/CD Approaches

### Approach 1: GitHub Actions ⭐ RECOMMENDED FOR STARTUPS

**Pros:**
- ✅ Zero maintenance (SaaS)
- ✅ Deep GitHub integration
- ✅ Large marketplace of actions
- ✅ Built-in secrets management
- ✅ Matrix builds (multi-platform)

**Cons:**
- ❌ Vendor lock-in
- ❌ Can get expensive at scale
- ❌ Harder to debug locally

**Best For:** Cloud-native startups, open-source projects

**Setup:**
```bash
# Workflow is automatically triggered on push
git push origin main

# View in GitHub Actions tab
# Secrets configured in: Settings → Secrets → Actions
```

### Approach 2: Jenkins

**Pros:**
- ✅ Infinite customizability
- ✅ On-premise or cloud
- ✅ Massive plugin ecosystem
- ✅ Fine-grained access control

**Cons:**
- ❌ High maintenance overhead
- ❌ Requires dedicated infrastructure
- ❌ Groovy syntax can be fragile

**Best For:** Enterprises with on-premise requirements, complex workflows

**Setup:**
```bash
# 1. Install Jenkins
# 2. Install required plugins (Kubernetes, Docker, Pipeline)
# 3. Create multibranch pipeline pointing to repo
# 4. Configure credentials (Docker registry, K8s)
# 5. Webhook from GitHub triggers builds
```

### Approach 3: GitOps (ArgoCD) ⭐ RECOMMENDED FOR KUBERNETES

**Pros:**
- ✅ Git as single source of truth
- ✅ Automatic drift detection
- ✅ Rollback via Git revert
- ✅ Kubernetes-native
- ✅ Enhanced security (pull model)

**Cons:**
- ❌ Steeper learning curve
- ❌ Requires Kubernetes
- ❌ CI still needed for build

**Best For:** Kubernetes deployments, regulated industries, large teams

**Setup:**
```bash
# 1. Install ArgoCD in cluster
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 3. Create application
kubectl apply -f ci-cd/argocd/application.yaml

# 4. Sync
argocd app sync sre-demo-api-prod
```

### Workflow Comparison

| Feature | GitHub Actions | Jenkins | ArgoCD |
|---------|----------------|---------|--------|
| **Maintenance** | None | High | Low |
| **Setup Time** | Minutes | Days | Hours |
| **Flexibility** | Medium | Extreme | Medium |
| **K8s Integration** | Good | Good | Excellent |
| **Git-centric** | Yes | No | Yes |
| **Drift Detection** | No | No | Yes |
| **Cost** | $$ | Self-hosted | Free |

---

## 📊 Observability

### The Four Golden Signals (Google SRE)

1. **Latency** - How long requests take
2. **Traffic** - How much demand on the system
3. **Errors** - Rate of failed requests
4. **Saturation** - How "full" the system is

### Metrics (Prometheus)

```bash
# Access Prometheus
http://localhost:9090

# Example queries:
# - Request rate: rate(http_requests_total[5m])
# - P95 latency: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
# - Error rate: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Logs (Loki)

```bash
# Access Grafana Explore
http://localhost:3000/explore

# Example LogQL queries:
# - All logs: {service="sre-demo-api"}
# - Errors only: {service="sre-demo-api"} |= "ERROR"
# - By correlation ID: {service="sre-demo-api"} | json | correlation_id="abc123"
```

### Traces (Jaeger)

```bash
# Access Jaeger UI
http://localhost:16686

# Find traces by:
# - Service name: sre-demo-api
# - Operation: GET /api/v1/items
# - Trace ID (from logs/correlation ID)
```

### Dashboards (Grafana)

Pre-configured dashboards in `observability/grafana/dashboards/`:
- **SRE Overview**: Four Golden Signals
- **Application Metrics**: Request rates, latency percentiles
- **Infrastructure**: CPU, memory, network
- **Error Tracking**: Error rates, types, trends

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit/ -v --cov=app --cov-report=html
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Load Testing (Locust)

```bash
# Start Locust web UI
locust -f tests/load/locustfile.py

# Or headless mode
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --html=report.html
```

### Chaos Engineering (Litmus)

```bash
# Kill random pod
kubectl apply -f tests/chaos/pod-delete.yaml

# Introduce network latency
kubectl apply -f tests/chaos/network-delay.yaml
```

---

## 🔒 Security

### Vulnerability Scanning

```bash
# Scan dependencies
safety check --file requirements.txt

# Scan container image
trivy image sre-demo-api:latest

# Scan Kubernetes manifests
trivy config k8s/
```

### RBAC (Role-Based Access Control)

```bash
# View service account permissions
kubectl auth can-i --list --as=system:serviceaccount:production:sre-demo-api

# Test specific permission
kubectl auth can-i get pods --as=system:serviceaccount:production:sre-demo-api
```

---

## 🚨 Troubleshooting

See comprehensive guide: [docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md)

### Quick Fixes

**Pod not starting?**
```bash
kubectl describe pod -n production <pod-name>
kubectl logs -n production <pod-name> --previous
```

**High latency?**
```bash
# Check if CPU throttled
kubectl top pods -n production

# Scale up
kubectl scale deployment/sre-demo-api --replicas=10 -n production
```

**Out of memory?**
```bash
# Check OOM kills
kubectl describe pod -n production <pod-name> | grep OOM

# Increase memory limit
kubectl set resources deployment sre-demo-api -n production \
  --limits=memory=1Gi --requests=memory=512Mi
```

---

## 📈 Performance Tuning

### Application-Level
- Use connection pooling for DB
- Implement caching (Redis)
- Enable HTTP/2
- Use async/await for I/O operations

### Kubernetes-Level
- Right-size resource requests/limits
- Use HPA for auto-scaling
- Implement PDB for high availability
- Use node affinity for performance-critical pods

### Network-Level
- Use Service Mesh (Istio/Linkerd) for advanced routing
- Enable HTTP keep-alive
- Use CDN for static assets

---

## 📚 Additional Documentation

- [Architecture Decision Records](docs/architecture/)
- [Runbooks](docs/runbooks/)
- [API Documentation](http://localhost:8000/docs)
- [Postman Collection](docs/api/postman_collection.json)

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Run tests: `pytest`
4. Run linters: `black app/ && flake8 app/`
5. Commit with semantic versioning
6. Submit pull request

---

## 📄 License

MIT License - See LICENSE file

---

## 💡 Key Takeaways for Senior SREs

1. **Immutability**: Containers are replaced, not patched
2. **Observability First**: Metrics, logs, traces from day one
3. **GitOps**: Infrastructure as code, Git as source of truth
4. **Security by Default**: Non-root, minimal images, RBAC
5. **Automated Recovery**: HPA, self-healing, circuit breakers
6. **Blameless Postmortems**: Learn from failures
7. **SLOs > SLAs**: Focus on user experience, not uptime percentage

---

**Questions?** Open an issue or contact the SRE team.
