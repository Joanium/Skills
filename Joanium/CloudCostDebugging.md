---
name: Cloud Cost Debugging & Optimization
trigger: aws bill, cloud costs, reduce aws costs, cost spike, unexpected bill, s3 costs, ec2 cost, data transfer costs, cloud cost optimization, rightsizing, reserved instances, savings plan, cloud spend, gcp billing, azure cost, cost anomaly, expensive cloud resource
description: Diagnose cloud cost spikes, find waste, and implement concrete savings. Use this skill when the user has an unexpectedly high cloud bill, wants to reduce AWS/GCP/Azure spend, or asks about rightsizing, reserved instances, spot instances, savings plans, or specific service costs. Focuses on AWS but principles apply broadly.
---

# ROLE
You are a cloud cost engineer (FinOps). You diagnose cost anomalies, identify waste, and implement savings — not just by recommendations but with specific actions and commands.

# STEP 1 — FIND THE SPIKE

```bash
# AWS Cost Explorer CLI — find what changed
aws ce get-cost-and-usage \
  --time-period Start=2024-03-01,End=2024-04-01 \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon EC2","Amazon S3","AWS Data Transfer"]}}' \
  | jq '.ResultsByTime[] | {date: .TimePeriod.Start, services: .Groups[] | {service: .Keys[0], cost: .Metrics.UnblendedCost.Amount}}'

# Enable Cost Anomaly Detection (free — catches spikes automatically)
aws ce create-anomaly-monitor \
  --anomaly-monitor '{"MonitorName":"AllServices","MonitorType":"DIMENSIONAL","MonitorDimension":"SERVICE"}'

aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "AlertMe",
    "MonitorArnList": ["<monitor-arn>"],
    "Subscribers": [{"Address": "you@company.com", "Type": "EMAIL"}],
    "Threshold": 100,
    "Frequency": "DAILY"
  }'
```

# TOP COST CULPRITS & FIXES

## EC2 — Compute

```bash
# Find idle instances (< 5% CPU over 14 days)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time $(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average

# Stop/terminate unused instances
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Find oversized instances (use AWS Compute Optimizer)
aws compute-optimizer get-ec2-instance-recommendations \
  --filters Name=Finding,Values=Overprovisioned

# Cost comparison: on-demand vs savings plans
# On-Demand m5.xlarge (us-east-1): ~$0.192/hr = $1,685/yr
# 1-yr Savings Plan (no upfront): ~$0.118/hr = $1,034/yr  (38% savings)
# 3-yr Savings Plan (all upfront): ~$0.074/hr = $648/yr   (61% savings)
```

## Spot Instances — 70-90% Savings

```python
# Use Spot for fault-tolerant workloads (workers, batch processing, ML training)
# Terraform example:
resource "aws_spot_instance_request" "worker" {
  ami                    = data.aws_ami.ubuntu.id
  spot_price             = "0.05"          # max bid price/hr
  instance_type          = "m5.xlarge"
  wait_for_fulfillment   = true
  spot_type              = "one-time"

  # Handle interruption gracefully in your app:
  # Poll instance metadata for termination notice:
  # curl http://169.254.169.254/latest/meta-data/spot/termination-time
}

# Or use Spot Fleet / EC2 Auto Scaling with mixed instances + Spot
resource "aws_autoscaling_group" "workers" {
  mixed_instances_policy {
    instances_distribution {
      on_demand_percentage_above_base_capacity = 20  # 20% on-demand, 80% spot
      spot_allocation_strategy                 = "price-capacity-optimized"
    }
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.worker.id
        version            = "$Latest"
      }
      override {
        instance_type = "m5.xlarge"
      }
      override {
        instance_type = "m5a.xlarge"   # fallback instance types
      }
    }
  }
}
```

## S3 — Storage

```bash
# Find large buckets
aws s3 ls --recursive s3://my-bucket | \
  awk '{total += $3} END {print total/1024/1024/1024 " GB"}'

# Check lifecycle rules
aws s3api get-bucket-lifecycle-configuration --bucket my-bucket

# Add lifecycle rule: move to Glacier after 90 days, delete after 365
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "ArchiveAndDelete",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"},
        {"Days": 180, "StorageClass": "DEEP_ARCHIVE"}
      ],
      "Expiration": {"Days": 365}
    }]
  }'

# S3 Intelligent Tiering for unpredictable access patterns
# (auto-moves objects to cheaper tiers — no retrieval fee for frequent access)
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket my-bucket \
  --id AllObjects \
  --intelligent-tiering-configuration '{
    "Id": "AllObjects",
    "Status": "Enabled",
    "Tierings": [
      {"Days": 90, "AccessTier": "ARCHIVE_ACCESS"},
      {"Days": 180, "AccessTier": "DEEP_ARCHIVE_ACCESS"}
    ]
  }'
```

## Data Transfer — Often the Hidden Cost

```
Biggest data transfer costs:
  1. EC2 → Internet (egress): $0.09/GB first 10TB
  2. Cross-region transfer: $0.02/GB
  3. Cross-AZ transfer: $0.01/GB (often missed!)
  4. NAT Gateway: $0.045/GB (+ $0.045/hr per AZ)

Fixes:
  - Use VPC Endpoints for S3/DynamoDB — free, eliminates NAT Gateway charges
  - Place resources in same AZ when possible (dev/staging)
  - CloudFront in front of S3 — reduces S3 egress (CloudFront to internet is cheaper)
  - Use Transfer Acceleration only when needed (has a premium)
```

```bash
# Create VPC Endpoint for S3 (eliminates NAT Gateway cost for S3 traffic)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345

# Find NAT Gateway costs
aws ce get-cost-and-usage \
  --time-period Start=2024-03-01,End=2024-04-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter '{"Dimensions":{"Key":"USAGE_TYPE","Values":["NatGateway-Hours","NatGateway-Bytes"]}}'
```

## RDS — Database

```bash
# Right-size: check CloudWatch metrics for CPU, connections, IOPS
# Look for: CPU < 10%, FreeableMemory > 80% of RAM → downsize

# Reserved Instances for RDS
# On-Demand db.r6g.xlarge: $0.48/hr = $4,205/yr
# 1-yr Reserved (all upfront): $2,617/yr = 38% savings

# Aurora Serverless v2 — pay per ACU, great for dev/staging
resource "aws_rds_cluster" "dev" {
  engine_mode = "provisioned"
  serverlessv2_scaling_configuration {
    min_capacity = 0.5   # ACUs — ~$0.06/hr minimum
    max_capacity = 4.0   # auto-scales up
  }
}

# Stop dev/staging RDS instances on nights/weekends
# (RDS can be stopped for 7 days, then auto-starts)
aws rds stop-db-instance --db-instance-identifier myapp-dev
```

# TAGGING STRATEGY — KNOW WHERE MONEY GOES

```bash
# Enforce tags on all resources (AWS Config rule)
# Without tags you can't do chargeback or debugging

# Required tags: environment, team, project, owner
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=environment,Value=production \
         Key=team,Value=backend \
         Key=project,Value=payments \
         Key=owner,Value=alice@company.com

# Activate tags for cost allocation in Billing Console
# Billing > Cost allocation tags > User-defined tags > Activate

# Query costs by tag
aws ce get-cost-and-usage \
  --time-period Start=2024-03-01,End=2024-04-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=team
```

# QUICK WINS PRIORITY ORDER

```
Priority  Action                              Typical Savings
─────────────────────────────────────────────────────────────
1         Terminate idle/unused resources      Varies (100%)
2         Savings Plans for baseline EC2/RDS   30-60%
3         S3 lifecycle rules + Intelligent Tier 40-70%
4         Right-size overprovisioned instances  20-40%
5         VPC Endpoints (eliminate NAT GW)      $0.045/GB saved
6         Spot instances for batch/workers      70-90%
7         Reserved DB instances                 30-40%
8         CloudFront for S3 egress              30-50%
9         Delete unused snapshots/AMIs/EIPs     Small but easy
10        Dev/staging: auto-shutdown nights      ~60% of dev cost
```

# BUDGET ALERTS

```bash
# Create budget with alert before you exceed it
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "Monthly AWS Limit",
    "BudgetLimit": {"Amount": "5000", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "team@company.com"
    }]
  }]'
```
