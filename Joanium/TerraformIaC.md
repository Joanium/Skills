---
name: Terraform Infrastructure as Code
trigger: terraform, tf files, infrastructure as code, iac, terraform plan, terraform apply, terraform module, tfvars, terraform state, aws terraform, gcp terraform, azure terraform, provision infrastructure, terraform destroy, remote state
description: Write, structure, and debug Terraform configurations for any cloud provider. Use this skill whenever the user mentions Terraform, .tf files, IaC, remote state, terraform plan/apply errors, or wants to provision cloud infrastructure with code. Covers project layout, modules, state management, variables, and CI/CD integration.
---

# ROLE
You are a senior DevOps/platform engineer specializing in Terraform. You write safe, reusable, DRY infrastructure code that can be applied without surprises.

# PROJECT STRUCTURE

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf          # environment entry point
│   │   ├── variables.tf
│   │   └── terraform.tfvars # env-specific values (gitignored for secrets)
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/                 # reusable VPC module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs-service/
│   └── rds/
└── backend.tf               # remote state config
```

# REMOTE STATE (ALWAYS USE IN TEAMS)

```hcl
# backend.tf — S3 + DynamoDB locking (AWS)
terraform {
  backend "s3" {
    bucket         = "my-company-tfstate"
    key            = "environments/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"   # prevents concurrent applies
    encrypt        = true
  }
}

# Create the backend resources first (bootstrap):
# aws s3api create-bucket --bucket my-company-tfstate --region us-east-1
# aws dynamodb create-table --table-name terraform-locks \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --billing-mode PAY_PER_REQUEST
```

# MODULE DESIGN

```hcl
# modules/ecs-service/variables.tf
variable "service_name" {
  type        = string
  description = "Name of the ECS service"
}

variable "container_image" {
  type        = string
  description = "Docker image URI, e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/app:latest"
}

variable "desired_count" {
  type        = number
  default     = 2
  description = "Number of task replicas"

  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 100
    error_message = "desired_count must be between 1 and 100."
  }
}

variable "environment" {
  type    = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

# modules/ecs-service/outputs.tf
output "service_arn" {
  value       = aws_ecs_service.this.id
  description = "ARN of the ECS service"
}

output "service_name" {
  value = aws_ecs_service.this.name
}
```

# VARIABLE PATTERNS

```hcl
# variables.tf — always type + description + validation
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type for the app servers"

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Only t3 instance family is allowed."
  }
}

# Sensitive variables — never hardcode secrets
variable "db_password" {
  type      = string
  sensitive = true   # hidden from logs and state output
}

# terraform.tfvars (gitignored) or pass via env:
# export TF_VAR_db_password="supersecret"
```

# COMMON RESOURCES

```hcl
# VPC with public + private subnets
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project}-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = var.environment != "prod"   # save cost in non-prod

  tags = local.common_tags
}

# Common tags (DRY)
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "platform-team"
  }
}

# RDS with encrypted storage
resource "aws_db_instance" "main" {
  identifier        = "${var.project}-${var.environment}"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "prod" ? 7 : 1
  deletion_protection     = var.environment == "prod"
  skip_final_snapshot     = var.environment != "prod"

  tags = local.common_tags
}
```

# SAFE WORKFLOW

```bash
# Initialize / update providers
terraform init
terraform init -upgrade   # upgrade provider versions

# Always plan before applying
terraform plan -out=tfplan
terraform show tfplan      # review what will change

# Apply only what was planned
terraform apply tfplan

# Target specific resource (use sparingly)
terraform plan -target=module.ecs-service
terraform apply -target=aws_security_group.web

# Destroy (requires explicit approval)
terraform destroy

# State inspection
terraform state list
terraform state show aws_s3_bucket.assets

# Import existing resource into state
terraform import aws_s3_bucket.assets my-existing-bucket-name

# Move resource in state without destroying
terraform state mv aws_s3_bucket.old aws_s3_bucket.new
```

# PREVENTING ACCIDENTAL DESTRUCTION

```hcl
# Lifecycle rules — protect production resources
resource "aws_db_instance" "main" {
  # ...
  lifecycle {
    prevent_destroy = true           # terraform destroy fails with error
    ignore_changes  = [password]     # don't flag password rotations as drift
    create_before_destroy = true     # for zero-downtime replacements
  }
}

# Use count/for_each to avoid force-replace
resource "aws_instance" "workers" {
  for_each      = toset(var.worker_names)   # changing a map key replaces only that instance
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  tags          = merge(local.common_tags, { Name = each.key })
}
```

# CI/CD INTEGRATION

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      id-token: write      # for OIDC auth to AWS
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-terraform
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0

      - run: terraform init
        working-directory: infrastructure/environments/prod

      - run: terraform validate

      - id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: infrastructure/environments/prod

      - uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Terraform Plan\n\`\`\`\n${{ steps.plan.outputs.stdout }}\n\`\`\``
            })

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production    # requires manual approval in GitHub
    steps:
      - run: terraform apply tfplan
```

# CHECKLIST
```
[ ] Remote state configured with locking
[ ] Sensitive vars marked sensitive = true, stored in secrets manager
[ ] All resources tagged with common_tags
[ ] prevent_destroy on stateful prod resources (RDS, S3)
[ ] validate + plan before every apply
[ ] Modules versioned with ~> constraints
[ ] OIDC auth for CI/CD (no long-lived AWS keys)
[ ] terraform.tfvars gitignored for files with secrets
```
