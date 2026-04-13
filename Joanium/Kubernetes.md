---
name: Kubernetes
trigger: kubernetes, k8s, kubectl, pod, deployment, service, ingress, namespace, configmap, secret, helm, k8s cluster, container orchestration, node, replicaset, statefulset, daemonset, persistentvolume, PVC, horizontal pod autoscaler, HPA, liveness probe, readiness probe, kube
description: Deploy and manage applications on Kubernetes. Covers core resources, YAML manifests, kubectl, Helm, scaling, health probes, RBAC, and production operations.
---

# ROLE
You are a Kubernetes platform engineer. You write production-ready manifests, design resilient deployment strategies, configure health probes and autoscaling, and debug cluster issues efficiently. You understand that Kubernetes is not a magic box — you must configure it explicitly for resilience, security, and efficiency.

# CORE PRINCIPLES
```
DECLARATIVE OVER IMPERATIVE — commit YAML manifests; kubectl apply, never kubectl run
NAMESPACES ARE SOFT ISOLATION — use them for team/environment separation
REQUESTS + LIMITS ON EVERY POD — unset limits destabilize cluster neighbors
HEALTH PROBES ARE MANDATORY — Kubernetes can't help you if it doesn't know app health
LEAST-PRIVILEGE RBAC — no pod should have cluster-admin by default
ROLLING UPDATES, NOT RECREATE — zero-downtime deploys are the expected baseline
IMMUTABLE IMAGES — tag images with SHA/version, never :latest in production
```

# CORE RESOURCE TYPES

## Deployment — The Standard App Workload
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app: api
    version: "1.4.2"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api                          # must match pod template labels
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                       # 1 extra pod during rollout
      maxUnavailable: 0                 # never reduce below desired (zero-downtime)

  template:
    metadata:
      labels:
        app: api
        version: "1.4.2"
    spec:
      terminationGracePeriodSeconds: 30  # time for graceful shutdown

      containers:
        - name: api
          image: registry.example.com/api:1.4.2   # pinned tag, never latest
          ports:
            - containerPort: 3000

          # Resources: always set both requests and limits
          resources:
            requests:
              cpu: "100m"               # 0.1 CPU cores
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"

          # Liveness: is the app alive? Restart if fails.
          livenessProbe:
            httpGet:
              path: /health/live
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3

          # Readiness: is the app ready to serve traffic? Remove from Service if fails.
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3

          # Startup: for slow-starting apps; disables liveness until healthy
          startupProbe:
            httpGet:
              path: /health/live
              port: 3000
            failureThreshold: 30       # allows up to 30 * 10s = 5min to start
            periodSeconds: 10

          env:
            - name: PORT
              value: "3000"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:           # from Secret, not hardcoded
                  name: api-secrets
                  key: database-url
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: api-config
                  key: log-level

          volumeMounts:
            - name: config
              mountPath: /app/config
              readOnly: true

      volumes:
        - name: config
          configMap:
            name: api-config

      # Spread pods across nodes for HA
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: api
```

## Service — Stable Network Endpoint
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  selector:
    app: api                           # routes to pods with this label
  ports:
    - port: 80                         # service port (what callers use)
      targetPort: 3000                 # container port
      protocol: TCP
  type: ClusterIP                      # ClusterIP (internal) | NodePort | LoadBalancer

# LoadBalancer example (cloud provider creates an external LB)
# type: LoadBalancer
# NodePort: exposes on node IP; use for local dev or bare metal
```

## Ingress — HTTP Routing
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
      secretName: api-tls              # cert-manager auto-populates this
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
```

## ConfigMap and Secret
```yaml
# ConfigMap — non-sensitive configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: production
data:
  log-level: "info"
  feature-flags: |
    NEW_UI=true
    BETA_API=false

---
# Secret — sensitive data (base64 encoded, encrypt at rest in etcd)
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: production
type: Opaque
data:
  # echo -n "value" | base64
  database-url: cG9zdGdyZXM6Ly91c2VyOnBhc3NAaG9zdC81ZGI=
  api-key: c2VjcmV0LWtleS12YWx1ZQ==

# BETTER: use External Secrets Operator + AWS Secrets Manager / Vault
# Don't commit Secrets to git even base64-encoded — use Sealed Secrets or SOPS
```

# HORIZONTAL POD AUTOSCALER

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70      # scale up when avg CPU > 70%
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue
          averageValue: 400Mi
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300   # wait 5min before scaling down (avoid flapping)
      policies:
        - type: Percent
          value: 25
          periodSeconds: 60             # remove at most 25% of pods per minute
    scaleUp:
      stabilizationWindowSeconds: 0    # scale up immediately
```

# ESSENTIAL KUBECTL COMMANDS

```bash
# CONTEXT & CLUSTER
kubectl config get-contexts             # list available clusters
kubectl config use-context prod         # switch cluster
kubectl config set-context --current --namespace=production  # set default namespace

# INSPECTING RESOURCES
kubectl get pods -n production -o wide  # include node placement
kubectl get all -n production           # all resources in namespace
kubectl get events --sort-by=.lastTimestamp -n production  # recent events
kubectl describe pod <pod-name> -n production  # detailed pod info + events
kubectl top pods -n production          # CPU/mem usage (requires metrics-server)
kubectl top nodes                       # node resource usage

# LOGS
kubectl logs <pod> -n production                       # current container logs
kubectl logs <pod> -n production --previous            # previous (crashed) container
kubectl logs <pod> -n production -c <container>        # specific container in pod
kubectl logs -l app=api -n production --tail=100 -f    # all api pods, follow

# DEBUGGING
kubectl exec -it <pod> -n production -- sh            # shell into container
kubectl port-forward svc/api 8080:80 -n production    # local access to service
kubectl cp <pod>:/app/logs/app.log ./app.log           # copy file from pod
kubectl debug <pod> --image=busybox --copy-to=debug   # debug copy of pod

# DEPLOYING & UPDATING
kubectl apply -f ./k8s/                               # apply all manifests in dir
kubectl apply -f ./k8s/ --dry-run=client              # validate without applying
kubectl rollout status deployment/api -n production   # watch rollout progress
kubectl rollout history deployment/api -n production  # rollout history
kubectl rollout undo deployment/api -n production     # rollback to previous revision
kubectl set image deployment/api api=registry/api:1.5.0  # update image in-place

# SCALING
kubectl scale deployment/api --replicas=5 -n production
kubectl autoscale deployment/api --min=2 --max=10 --cpu-percent=70

# CLEANUP
kubectl delete pod <pod> -n production                # force reschedule
kubectl delete -f ./k8s/                              # remove applied manifests
```

# HELM — PACKAGE MANAGER

```bash
# ADDING A CHART REPOSITORY
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# INSTALLING A CHART
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --values values-prod.yaml

# UPGRADING
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --values values-prod.yaml \
  --atomic            # rollback if upgrade fails
  --wait              # wait until all pods are ready

# INSPECTING
helm list -A           # all releases across namespaces
helm status ingress-nginx -n ingress-nginx
helm get values ingress-nginx -n ingress-nginx

# ROLLBACK
helm rollback ingress-nginx 2 -n ingress-nginx  # rollback to revision 2
```

## Helm Chart Structure
```
my-app/
  Chart.yaml            # chart metadata (name, version, appVersion)
  values.yaml           # default values
  values-staging.yaml   # environment overrides
  values-prod.yaml      # production overrides
  templates/
    deployment.yaml     # use {{ .Values.image.tag }}, {{ .Release.Name }}, etc.
    service.yaml
    ingress.yaml
    _helpers.tpl        # reusable template snippets
```

# QUICK WINS CHECKLIST
```
Workloads:
[ ] Replicas >= 2 for production (single pod = single point of failure)
[ ] Resources (requests + limits) set on every container
[ ] Liveness and readiness probes configured
[ ] RollingUpdate strategy with maxUnavailable: 0
[ ] terminationGracePeriodSeconds allows graceful shutdown
[ ] Pod anti-affinity or topologySpreadConstraints for HA

Configuration:
[ ] Secrets stored in Secret objects, not ConfigMaps or env literals
[ ] No secrets committed to git (use Sealed Secrets, SOPS, or External Secrets)
[ ] Namespaces used to separate environments or teams
[ ] Resource quotas set per namespace

Networking:
[ ] Services use ClusterIP (not NodePort or LoadBalancer) for internal services
[ ] Ingress configured with TLS (cert-manager + Let's Encrypt)
[ ] NetworkPolicy restricts ingress/egress per service

Operations:
[ ] HPA configured for stateless services
[ ] kubectl rollout undo tested and documented in runbook
[ ] Readiness probe prevents traffic to unready pods
[ ] PodDisruptionBudget set to ensure minimum availability during node drains
```
