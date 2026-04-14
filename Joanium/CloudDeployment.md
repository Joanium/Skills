---
name: Cloud Deployment
trigger: deploy to AWS, deploy to GCP, deploy to cloud, EC2, ECS, Kubernetes, Fly.io, Railway, infrastructure as code, Terraform, cloud architecture, VPC, load balancer, RDS, ElastiCache, production infrastructure
description: Twelfth skill in the build pipeline. Covers deploying to production cloud infrastructure — managed services selection (RDS, ElastiCache, ECS), infrastructure as code with Terraform, networking, and cost-efficient production architectures.
prev_skill: 11-DevOpsCICD.md
next_skill: 13-MonitoringObservability.md
---

# ROLE
You are a cloud infrastructure engineer. You provision reliable, cost-efficient infrastructure that can grow with the product. You prefer managed services over self-managed. You know that the right architecture at 100 users is different from the right architecture at 100,000 users, and you start appropriately sized.

# CORE PRINCIPLES
```
USE MANAGED SERVICES — RDS over self-managed PostgreSQL, ElastiCache over self-managed Redis
START SMALL, SCALE PROVEN BOTTLENECKS — don't provision for imagined scale
INFRASTRUCTURE AS CODE — never click through consoles; use Terraform or CDK
EVERYTHING IN A VPC — databases and internal services are never public
SEPARATE ACCOUNTS FOR PROD AND NON-PROD — blast radius containment
LEAST-PRIVILEGE IAM — each service gets only the permissions it needs
```

# STEP 1 — PLATFORM SELECTION

```
DECISION TREE:

  < 5 engineers, early-stage startup, want to move fast?
    → Fly.io or Railway (PaaS — deploys from Dockerfile, managed everything)
    → Zero infrastructure management, built-in Postgres + Redis, git push deploy
    → Costs: $50-200/month up to meaningful traffic

  Growing startup, need more control, AWS familiarity?
    → AWS with ECS Fargate (managed containers, no EC2 management)
    → RDS PostgreSQL + ElastiCache Redis + S3 + CloudFront
    → Costs: $200-1000/month for production-grade setup

  Large scale, multiple services, dedicated infra team?
    → AWS EKS or GKE (Kubernetes) + full managed service suite
    → Costs: $1000+/month, high operational complexity

MANAGED PLATFORM COMPARISON:
  Platform      Pros                           Cons
  ──────────    ─────────────────────────────  ────────────────────────
  Fly.io        Global edge, fast deploys      Smaller ecosystem
  Railway       Easiest DX, auto-HTTPS         Less control at scale
  Render        Heroku-like, free tier         Cold starts on free
  AWS ECS       Full control, every AWS svc    More setup required
  Google Run    Per-request billing, scales 0  Cold starts, GCP learning
```

# STEP 2 — SIMPLE PRODUCTION ARCHITECTURE (FLY.IO)

```toml
# fly.toml — deploy a Dockerized Node.js API
app = "yourapp-api"
primary_region = "sin"  # Singapore — close to Chennai

[build]
  dockerfile = "Dockerfile"

[env]
  NODE_ENV = "production"
  PORT = "3000"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false  # keep warm — avoid cold starts in production

  [[http_service.checks]]
    path = "/health"
    interval = "30s"
    timeout = "10s"

[[vm]]
  memory = "1gb"
  cpu_kind = "shared"
  cpus = 1

[mounts]  # persistent volume for temp storage (not for primary data)
  source = "tmp"
  destination = "/tmp/transcode"

# Scaling (set after you know your traffic):
# fly scale count 2  -- two instances, always-on HA
# fly scale vm performance-2x  -- upgrade machine size
```

```bash
# Fly.io setup commands:
fly launch              # initialize app from Dockerfile
fly postgres create     # managed PostgreSQL
fly redis create        # managed Redis via Upstash
fly secrets set JWT_SECRET="$(openssl rand -hex 32)"
fly secrets set DATABASE_URL="postgresql://..."
fly deploy              # build + push + deploy
fly status              # check deployment health
fly logs                # tail production logs
```

# STEP 3 — PRODUCTION AWS ARCHITECTURE

```
ARCHITECTURE DIAGRAM:
  Internet
    │
    ▼
  Route 53 (DNS)
    │
    ▼
  CloudFront (CDN)
    │                    │
    ▼                    ▼
  ALB (Load Balancer)   S3 (Static assets, media)
    │
    ▼ (only port 443, HTTPS)
  ECS Fargate (API containers — in private subnet)
    │
    ├── RDS PostgreSQL (private subnet, no public access)
    ├── ElastiCache Redis (private subnet)
    └── ECS Fargate (Workers — transcoding, email)

NETWORKING:
  VPC CIDR: 10.0.0.0/16
    Public subnets:   10.0.1.0/24, 10.0.2.0/24   (ALB, NAT Gateway)
    Private subnets:  10.0.3.0/24, 10.0.4.0/24   (ECS, RDS, Redis)

  Security Groups:
    ALB SG:       inbound 443 from 0.0.0.0/0
    API SG:       inbound 3000 from ALB SG only
    RDS SG:       inbound 5432 from API SG only
    Redis SG:     inbound 6379 from API SG only
    Worker SG:    inbound none (workers initiate outbound only)
```

# STEP 4 — TERRAFORM INFRASTRUCTURE AS CODE

```hcl
# infrastructure/main.tf

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "yourapp-terraform-state"
    key    = "production/terraform.tfstate"
    region = "ap-south-1"
  }
}

provider "aws" { region = "ap-south-1" }  # Mumbai — closest to Chennai

# ─── VPC ─────────────────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "yourapp-vpc"
  cidr = "10.0.0.0/16"

  azs              = ["ap-south-1a", "ap-south-1b"]
  private_subnets  = ["10.0.3.0/24", "10.0.4.0/24"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true  # cost saving — use 2 for HA
  enable_dns_hostnames = true
}

# ─── RDS PostgreSQL ───────────────────────────────────────────────────────────
resource "aws_db_instance" "postgres" {
  identifier        = "yourapp-db"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.t4g.medium"  # 2 vCPU, 4GB RAM — start here
  allocated_storage = 100              # GB
  storage_encrypted = true

  db_name  = "appdb"
  username = "dbadmin"
  password = var.db_password  # from Terraform variables / Secrets Manager

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7       # 7 days of automatic backups
  deletion_protection     = true    # prevents accidental destroy in prod
  multi_az                = false   # enable for HA ($$ doubles cost)

  performance_insights_enabled = true  # free tier — helps diagnose slow queries
}

# ─── ElastiCache Redis ────────────────────────────────────────────────────────
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "yourapp-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t4g.small"  # 1.37GB — enough for sessions + cache
  num_cache_nodes      = 1

  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ─── ECS CLUSTER ──────────────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "yourapp"
  setting { name = "containerInsights", value = "enabled" }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"    # 0.5 vCPU
  memory                   = "1024"   # 1GB

  container_definitions = jsonencode([{
    name  = "api"
    image = "ghcr.io/yourorg/yourapp/api:latest"
    portMappings = [{ containerPort = 3000 }]
    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "PORT",     value = "3000" },
    ]
    secrets = [  # pull from Secrets Manager at runtime
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.db_url.arn },
      { name = "JWT_SECRET",   valueFrom = aws_secretsmanager_secret.jwt.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"  = "/ecs/api"
        "awslogs-region" = "ap-south-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
    healthCheck = {
      command = ["CMD-SHELL", "wget -q -O - http://localhost:3000/health || exit 1"]
      interval = 30, timeout = 10, retries = 3
    }
  }])

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn
}

resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2  # always 2 instances for HA

  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.api.id]
  }

  load_balancer {
    target_group_arn = aws_alb_target_group.api.arn
    container_name   = "api"
    container_port   = 3000
  }

  deployment_circuit_breaker {
    enable   = true   # auto-rollback if deployment fails health checks
    rollback = true
  }
}

# ─── S3 + CLOUDFRONT ──────────────────────────────────────────────────────────
resource "aws_s3_bucket" "media" {
  bucket = "yourapp-media-production"
}

resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["https://yourapp.com"]
    max_age_seconds = 3600
  }
}

resource "aws_cloudfront_distribution" "media" {
  origin {
    domain_name = aws_s3_bucket.media.bucket_regional_domain_name
    origin_id   = "S3-media"
  }
  enabled         = true
  is_ipv6_enabled = true

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-media"
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 86400    # 1 day
    max_ttl     = 31536000 # 1 year
  }
}
```

# STEP 5 — COST OPTIMIZATION

```
COST BREAKDOWN (AWS, Mumbai, estimated):
  ECS Fargate: 2 × 0.5vCPU/1GB → ~$30/month
  RDS t4g.medium (Multi-AZ off) → ~$60/month
  ElastiCache t4g.small → ~$25/month
  ALB → ~$20/month
  S3 (100GB) → ~$3/month
  CloudFront (1TB transfer) → ~$85/month
  NAT Gateway → ~$35/month
  ─────────────────────────────────
  TOTAL: ~$260/month for production-grade infrastructure

COST REDUCTION TIPS:
  ✅ Reserved Instances for RDS (1-year) → 40% savings on DB
  ✅ Savings Plans for ECS → 30-40% savings on compute
  ✅ Use Graviton (ARM) instances — t4g vs t3: same price, 20% faster
  ✅ Cloudflare R2 instead of S3 + CloudFront → no egress fees (saves $$$)
  ✅ Compress assets at origin — S3 stores compressed; CloudFront serves compressed
  ✅ S3 Intelligent Tiering for media older than 30 days → auto moves to cheaper tier
```

# CHECKLIST — Before Moving to Monitoring

```
✅ Platform chosen (Fly.io for speed, AWS for control)
✅ Infrastructure as code written (fly.toml or Terraform)
✅ Networking: all databases in private subnets, no public exposure
✅ Security groups: least-privilege ingress rules
✅ Secrets in managed secret store (not environment variables in code)
✅ S3 + CloudFront configured for media serving
✅ RDS backups enabled (7+ day retention)
✅ ECS deployment circuit breaker enabled (auto-rollback)
✅ Cost estimate done — within budget
✅ DNS configured and HTTPS enforced
→ NEXT: 13-MonitoringObservability.md
```
