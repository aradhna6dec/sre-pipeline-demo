# ==============================================================================
# Troubleshooting Guide - Production Issues
# ==============================================================================
# Senior SRE Decision Tree for Debugging Production Problems
# ==============================================================================

## Table of Contents
1. [Quick Diagnosis](#quick-diagnosis)
2. [Common Failure Scenarios](#common-failure-scenarios)
3. [Debug Commands](#debug-commands)
4. [Escalation Procedures](#escalation-procedures)

---

## Quick Diagnosis

### Is the Service Down?

```bash
# Check if pods are running
kubectl get pods -n production -l app=sre-demo-api

# Expected: All pods in "Running" state with READY 1/1
```

**Decision Tree:**
- ✅ All pods Running → [Check Latency Issues](#high-latency)
- ❌ CrashLoopBackOff → [Pod Crashing](#crashloopbackoff)
- ❌ ImagePullBackOff → [Image Pull Failed](#imagepullbackoff)
- ❌ Pending → [Scheduling Issues](#pod-pending)
- ❌ OOMKilled → [Out of Memory](#oomkilled)

---

## Common Failure Scenarios

### 1. CrashLoopBackOff

**Symptom:** Pod starts, crashes immediately, restarts in loop

**Diagnosis:**
```bash
# View recent logs
kubectl logs -n production <pod-name> --previous

# Describe pod for events
kubectl describe pod -n production <pod-name>

# Common causes in output:
# - "ModuleNotFoundError" → Missing dependency
# - "Connection refused" → Database/Redis unavailable
# - "PermissionError" → File permission issue (rootless container)
# - "Error: Address already in use" → Port conflict
```

**Resolution Steps:**
1. Check application logs for stack trace
2. Verify ConfigMap/Secret are correctly mounted
3. Check database/Redis connectivity:
   ```bash
   kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -n production
   # Inside debug pod:
   nc -zv postgres.db 5432
   nc -zv redis.cache 6379
   ```
4. Verify environment variables:
   ```bash
   kubectl exec -n production <pod-name> -- env | grep DATABASE
   ```

**Rollback if needed:**
```bash
kubectl rollout undo deployment/sre-demo-api -n production
kubectl rollout status deployment/sre-demo-api -n production
```

---

### 2. OOMKilled (Exit Code 137)

**Symptom:** Pod memory usage exceeds limit

**Diagnosis:**
```bash
# Check pod status
kubectl describe pod -n production <pod-name> | grep -A 5 "Last State"

# Output will show:
#   Last State:     Terminated
#     Reason:       OOMKilled
#     Exit Code:    137

# Check current memory usage
kubectl top pods -n production -l app=sre-demo-api

# Check metrics history (if Prometheus is running)
# Go to Grafana → SRE Dashboard → Memory Usage panel
```

**Root Causes:**
1. **Memory Leak** → Check for unbounded caching, circular references
2. **Traffic Spike** → HPA didn't scale fast enough
3. **Java Heap Too Large** → `-Xmx` setting exceeds container limit

**Resolution:**
```bash
# Immediate fix: Increase memory limit
kubectl patch deployment sre-demo-api -n production -p '
spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          limits:
            memory: "1Gi"  # Increased from 512Mi
'

# Long-term fix: Investigate memory leak
# 1. Enable memory profiling
# 2. Analyze with py-spy or memory_profiler
# 3. Review code for unclosed connections, large data structures
```

**Prevention:**
- Set appropriate `requests` and `limits`
- Configure HPA to scale before memory exhaustion
- Implement circuit breakers for external services

---

### 3. High Latency (P99 > 1s)

**Symptom:** API responses slow, users complaining

**Diagnosis:**
```bash
# Check current latency in Prometheus
# Query: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Check if CPU throttling is occurring
kubectl describe pod -n production <pod-name> | grep -i throttl

# Check for slow database queries
# Access database metrics or logs
```

**Common Causes:**
1. **CPU Throttling** → Pod hitting CPU limit
   ```bash
   # Increase CPU limit
   kubectl set resources deployment sre-demo-api -n production \
     --limits=cpu=1000m --requests=cpu=500m
   ```

2. **Database Slow Queries**
   - Enable query logging
   - Check for missing indexes
   - Analyze slow query log

3. **External API Timeouts**
   - Check circuit breaker status
   - Verify external service health
   - Implement retries with backoff

4. **Cold Start** (after scaling up)
   - Implement readiness probe with warmup
   - Pre-warm caches during startup

**Immediate Mitigation:**
```bash
# Scale up replicas to distribute load
kubectl scale deployment sre-demo-api -n production --replicas=10

# If HPA is active, check why it didn't scale:
kubectl get hpa -n production
kubectl describe hpa sre-demo-api-hpa -n production
```

---

### 4. Pod Pending (Not Scheduling)

**Symptom:** Pod stuck in "Pending" state

**Diagnosis:**
```bash
kubectl describe pod -n production <pod-name>

# Common messages:
# - "0/5 nodes available: Insufficient cpu" → Need more nodes
# - "0/5 nodes available: node(s) had taint" → Node taints
# - "pod has unbound immediate PersistentVolumeClaims" → Storage issue
```

**Resolution:**
```bash
# For insufficient resources:
# 1. Scale cluster (add nodes)
# 2. Reduce resource requests temporarily
# 3. Delete unused pods

# For taint issues:
kubectl get nodes -o json | jq '.items[].spec.taints'
# Add tolerations if needed

# For storage issues:
kubectl get pvc -n production
kubectl get pv
```

---

### 5. ImagePullBackOff

**Symptom:** Cannot pull container image

**Diagnosis:**
```bash
kubectl describe pod -n production <pod-name>

# Common errors:
# - "unauthorized: authentication required" → Registry auth issue
# - "not found" → Image tag doesn't exist
# - "manifest unknown" → Image deleted from registry
```

**Resolution:**
```bash
# Verify image exists
docker pull your-registry.io/sre-demo-api:main-abc123

# Check image pull secrets
kubectl get secrets -n production | grep regcred

# If missing, create:
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.io \
  --docker-username=<user> \
  --docker-password=<pass> \
  -n production

# Patch deployment to use secret
kubectl patch serviceaccount default -n production -p '
imagePullSecrets:
- name: regcred
'
```

---

### 6. Service Unavailable (503 Errors)

**Symptom:** LoadBalancer returns 503

**Diagnosis:**
```bash
# Check if pods are ready
kubectl get pods -n production -l app=sre-demo-api

# Check service endpoints
kubectl get endpoints -n production sre-demo-api

# Should show pod IPs. If empty:
# → No pods are passing readiness probe
```

**Resolution:**
```bash
# Check readiness probe logs
kubectl logs -n production <pod-name> --tail=100 | grep readiness

# Common fixes:
# 1. Database connection failed → Fix DB
# 2. Readiness probe too strict → Adjust threshold
# 3. All pods restarting → Check CrashLoopBackOff section
```

---

### 7. Network Policy Blocking Traffic

**Symptom:** Cannot connect to database/external services

**Diagnosis:**
```bash
# List network policies
kubectl get networkpolicies -n production

# Test connectivity from pod
kubectl exec -it -n production <pod-name> -- curl -v http://postgres.db:5432
```

**Resolution:**
```bash
# Temporarily allow all egress for debugging
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress-temp
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: sre-demo-api
  policyTypes:
  - Egress
  egress:
  - {}
EOF

# After debugging, remove and fix proper policy
```

---

## Debug Commands Reference

### Logs
```bash
# Real-time logs
kubectl logs -f -n production <pod-name>

# Previous container logs (if crashed)
kubectl logs -n production <pod-name> --previous

# All containers in pod
kubectl logs -n production <pod-name> --all-containers=true

# Logs from last 1 hour
kubectl logs -n production <pod-name> --since=1h

# Export logs to file
kubectl logs -n production <pod-name> > debug.log
```

### Exec into Pod
```bash
# For standard image (with shell)
kubectl exec -it -n production <pod-name> -- /bin/bash

# For distroless (no shell - use ephemeral container)
kubectl debug -it -n production <pod-name> \
  --image=nicolaka/netshoot \
  --target=api

# Run one-off command
kubectl exec -n production <pod-name> -- ps aux
```

### Port Forwarding
```bash
# Forward pod port to local
kubectl port-forward -n production <pod-name> 8000:8000

# Access: http://localhost:8000

# Forward service
kubectl port-forward -n production svc/sre-demo-api 8000:80
```

### Resource Usage
```bash
# Current usage
kubectl top pods -n production

# Node usage
kubectl top nodes

# Detailed pod resource info
kubectl describe pod -n production <pod-name> | grep -A 10 "Requests:\|Limits:"
```

---

## Escalation Procedures

### Severity Levels

**P0 (Critical - Service Down)**
- All pods down OR Error rate > 50%
- Immediate page to on-call SRE
- Create war room in Slack #incidents
- Update status page

**P1 (High - Degraded Performance)**
- High latency (P99 > 2s) OR Error rate > 10%
- Notify SRE team in #sre-alerts
- Create incident ticket
- Start investigation

**P2 (Medium - Minor Issue)**
- Single pod failing OR Low error rate (1-5%)
- Monitor for 15 minutes
- Self-heal or restart pod
- Document in post-mortem

### Contact Information
- On-Call: PagerDuty rotation
- Slack: #sre-team, #incidents
- Runbook: https://runbooks.company.com

---

## Post-Incident

After resolving an issue:
1. Document what happened
2. Create postmortem (blameless)
3. Add/update alerts
4. Update runbooks
5. Create Jira tickets for prevention work
