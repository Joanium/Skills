---
name: Kubernetes Patterns
trigger: kubernetes deployment, k8s, helm chart, pod config, ingress, hpa, kubernetes production, k8s manifests, kubernetes scaling, namespace, configmap, secret, deployment strategy, kubernetes architecture, k8s cluster
description: Deploy, configure, and operate production-grade Kubernetes workloads. Covers Deployments, Services, Ingress, ConfigMaps, Secrets, HPA, resource limits, Helm, RBAC, and production readiness patterns.
---

# ROLE
You are a senior platform engineer specializing in Kubernetes. Your job is to help teams run reliable, scalable, observable workloads on Kubernetes — with zero ambiguity about configuration choices and clear reasoning for each pattern.

# CORE CONCEPTS MAP
```
Cluster        → group of nodes (VMs) managed by the control plane
Node           → a VM running kubelet + container runtime
Pod            → smallest deployable unit; 1+ containers sharing network/storage
Deployment     → manages ReplicaSets; handles rolling updates and rollbacks
Service        → stable DNS name + load balancing in front of pods
Ingress        → HTTP/HTTPS routing from outside the cluster to Services
ConfigMap      → inject non-secret config into pods
Secret         → inject sensitive config (base64-encoded, not encrypted by default)
Namespace      → virtual cluster; isolate teams/environments
HPA            → Horizontal Pod Autoscaler; scale pods on CPU/memory/custom metrics
PVC/PV         → persistent storage for stateful workloads
```

# DEPLOYMENT MANIFEST — PRODUCTION TEMPLATE
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
  labels:
    app: api-server
    version: "1.4.2"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # allow 1 extra pod during update
      maxUnavailable: 0    # never take a pod down before new one is ready
  template:
    metadata:
      labels:
        app: api-server
        version: "1.4.2"
    spec:
      # Always pull latest (avoid cached stale images)
      imagePullPolicy: IfNotPresent
      
      # Graceful shutdown
      terminationGracePeriodSeconds: 60
      
      containers:
        - name: api-server
          image: myorg/api-server:1.4.2   # ALWAYS pin tag — never use :latest in prod
          ports:
            - containerPort: 3000
          
          # Resource limits — ALWAYS set these
          resources:
            requests:
              cpu: "250m"        # 0.25 vCPU guaranteed
              memory: "256Mi"    # 256 MB guaranteed
            limits:
              cpu: "1000m"       # 1 vCPU max
              memory: "512Mi"    # 512 MB max — OOMKilled if exceeded
          
          # Liveness — restart if unhealthy
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 3
          
          # Readiness — only route traffic when ready
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 2
          
          # Startup probe — give slow apps time to init before liveness kicks in
          startupProbe:
            httpGet:
              path: /health
              port: 3000
            failureThreshold: 30    # 30 * 10s = 5 min max startup time
            periodSeconds: 10
          
          # Inject config
          envFrom:
            - configMapRef:
                name: api-server-config
            - secretRef:
                name: api-server-secrets
          
          env:
            - name: NODE_ENV
              value: "production"
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name   # inject pod name for logging
      
      # Spread pods across nodes for resilience
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: api-server
      
      # Don't schedule on same node as another replica (soft rule)
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: api-server
                topologyKey: kubernetes.io/hostname
```

# SERVICE — EXPOSE PODS
```yaml
# ClusterIP — internal only (default)
apiVersion: v1
kind: Service
metadata:
  name: api-server
  namespace: production
spec:
  selector:
    app: api-server
  ports:
    - name: http
      port: 80
      targetPort: 3000
  type: ClusterIP

# Service types:
#   ClusterIP    → internal cluster DNS only (api-server.production.svc.cluster.local)
#   NodePort     → expose on each node's IP:port (dev/testing only)
#   LoadBalancer → provision cloud load balancer (for non-HTTP services)
#   Ingress      → use this for HTTP/HTTPS instead of LoadBalancer
```

# INGRESS — HTTP ROUTING
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
      secretName: api-tls-cert    # cert-manager populates this
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /api/v1
            pathType: Prefix
            backend:
              service:
                name: api-server
                port:
                  number: 80
          - path: /api/v2
            pathType: Prefix
            backend:
              service:
                name: api-server-v2
                port:
                  number: 80
```

# CONFIGMAP & SECRETS
```yaml
# ConfigMap — non-sensitive config
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-server-config
  namespace: production
data:
  LOG_LEVEL: "info"
  REDIS_HOST: "redis.production.svc.cluster.local"
  MAX_CONNECTIONS: "100"

---
# Secret — sensitive values (base64 encoded, not encrypted — use Sealed Secrets or ESO for real encryption)
apiVersion: v1
kind: Secret
metadata:
  name: api-server-secrets
  namespace: production
type: Opaque
data:
  DATABASE_URL: cG9zdGdyZXM6Ly91c2VyOnBhc3NAaG9zdC9kYg==   # base64
  JWT_SECRET: c3VwZXJzZWNyZXRrZXk=

# BETTER: Use External Secrets Operator to pull from AWS Secrets Manager / Vault
# Never commit Secret manifests to git — even base64 is trivially decoded
```

# HORIZONTAL POD AUTOSCALER
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70    # scale up when avg CPU > 70%
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60     # wait 60s before scaling up again
    scaleDown:
      stabilizationWindowSeconds: 300    # wait 5min before scaling down (avoid flapping)
```

# HELM — PACKAGE MANAGER
```
Chart structure:
  my-app/
    Chart.yaml           # metadata (name, version, appVersion)
    values.yaml          # default values
    values-prod.yaml     # production overrides
    templates/
      deployment.yaml
      service.yaml
      ingress.yaml
      hpa.yaml
      _helpers.tpl       # reusable template functions

Key commands:
  helm repo add myrepo https://charts.example.com
  helm install my-app ./my-app -f values-prod.yaml -n production
  helm upgrade my-app ./my-app -f values-prod.yaml --atomic   # rollback on failure
  helm rollback my-app 1                                       # rollback to revision 1
  helm diff upgrade my-app ./my-app -f values-prod.yaml        # preview changes

values.yaml pattern:
  image:
    repository: myorg/api-server
    tag: "1.4.2"
    pullPolicy: IfNotPresent
  replicaCount: 3
  resources:
    requests: { cpu: 250m, memory: 256Mi }
    limits:   { cpu: 1000m, memory: 512Mi }
```

# NAMESPACE & RBAC
```yaml
# Namespace per environment or team
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production

---
# ServiceAccount for workload identity
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-server
  namespace: production

---
# Role — scoped to namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-server-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]

---
# Bind role to service account
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-server-rolebinding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: api-server
    namespace: production
roleRef:
  kind: Role
  name: api-server-role
  apiGroup: rbac.authorization.k8s.io
```

# DEBUGGING RUNBOOK
```bash
# Pod not starting?
kubectl get pods -n production
kubectl describe pod <pod-name> -n production    # look at Events section
kubectl logs <pod-name> -n production --previous # logs from crashed container

# CrashLoopBackOff → liveness probe failing, OOMKilled, or app crashing on start
kubectl describe pod <pod-name> | grep -A5 "Last State"

# ImagePullBackOff → wrong image name/tag or missing imagePullSecret
kubectl describe pod <pod-name> | grep "image"

# Pending pod → insufficient resources or no matching node
kubectl describe pod <pod-name> | grep -A10 "Events"
kubectl get nodes -o wide

# Check resource usage
kubectl top pods -n production
kubectl top nodes

# Exec into pod
kubectl exec -it <pod-name> -n production -- /bin/sh

# Port-forward for local debugging
kubectl port-forward pod/<pod-name> 8080:3000 -n production
```

# PRODUCTION READINESS CHECKLIST
```
[ ] Resource requests AND limits set on all containers
[ ] Liveness, readiness, and startup probes configured
[ ] Image tags pinned (no :latest)
[ ] Replicas >= 3 for HA
[ ] PodDisruptionBudget set (protect against node drain)
[ ] HPA configured with sensible min/max
[ ] Secrets NOT stored in git (use Sealed Secrets or ESO)
[ ] RBAC: least-privilege service accounts
[ ] Network policies restricting pod-to-pod traffic
[ ] Resource quotas set per namespace
[ ] Logging to stdout/stderr (not files)
[ ] Graceful shutdown handled (SIGTERM → drain, wait, exit)
[ ] Topology spread or pod anti-affinity for resilience
```
