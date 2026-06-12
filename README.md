# Microservice Health Monitor

> A production-grade cloud-native platform featuring **3 microservices**, full **AWS infrastructure via Terraform**, **CI/CD with GitHub Actions**, **CloudWatch monitoring with SNS alerts**, and a **real-time health dashboard** — all designed as a portfolio-ready DevOps project.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-6C5CE7?style=flat-square)
![AWS](https://img.shields.io/badge/Cloud-AWS-FF9900?style=flat-square)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat-square)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat-square)
![Docker](https://img.shields.io/badge/Containers-Docker-2496ED?style=flat-square)
![Python](https://img.shields.io/badge/Backend-Python%2FFlask-3776AB?style=flat-square)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GitHub Actions                             │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │  Lint    │──▶│  Test    │──▶│  Build   │──▶│  Deploy to AWS  │  │
│  └─────────┘   └──────────┘   └──────────┘   └─────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────── AWS Cloud ──────────────────────────────┐
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  VPC (10.0.0.0/16)                                          │   │
│  │  ┌─────────────────────┐  ┌──────────────────────────────┐  │   │
│  │  │  Public Subnets     │  │  Private Subnets              │  │   │
│  │  │  ┌───────────────┐  │  │  ┌──────────┐ ┌──────────┐   │  │   │
│  │  │  │  ALB (HTTP)   │──┼──┼─▶│  ECS     │ │  ECS     │   │  │   │
│  │  │  │  Path Routing  │  │  │  │  Fargate │ │  Fargate │   │  │   │
│  │  │  └───────────────┘  │  │  │  user-svc│ │  order-svc│  │  │   │
│  │  │  ┌───────────────┐  │  │  └──────────┘ └──────────┘   │  │   │
│  │  │  │  NAT Gateway  │  │  │  ┌──────────┐                │  │   │
│  │  │  └───────────────┘  │  │  │  ECS     │                │  │   │
│  │  └─────────────────────┘  │  │  Fargate │                │  │   │
│  │                           │  │  notif-svc│               │  │   │
│  │                           │  └──────────┘                │  │   │
│  │                           └──────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────┐  ┌────────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │  ECR   │  │ CloudWatch │  │    SNS    │  │  S3 + CloudFront │   │
│  │ Images │  │  Alarms +  │  │  Email    │  │  Dashboard       │   │
│  │        │  │  Dashboard │  │  Alerts   │  │                  │   │
│  └────────┘  └────────────┘  └───────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer              | Technology                                    |
|--------------------|-----------------------------------------------|
| **Backend**        | Python 3.12, Flask, Gunicorn                  |
| **Containers**     | Docker (multi-stage builds)                   |
| **Orchestration**  | AWS ECS Fargate                               |
| **Registry**       | AWS ECR (image scanning, lifecycle policies)  |
| **Load Balancing** | AWS ALB (path-based routing)                  |
| **Networking**     | VPC, Public/Private Subnets, NAT Gateway, SGs |
| **Monitoring**     | CloudWatch Logs, Alarms, Dashboard            |
| **Alerting**       | AWS SNS (email notifications)                 |
| **IaC**            | Terraform (6 modular modules)                 |
| **CI/CD**          | GitHub Actions (OIDC auth, change detection)  |
| **Frontend**       | Vanilla HTML/CSS/JS (S3 + CloudFront)         |
| **Security**       | IAM least-privilege, non-root containers, OIDC|

## Project Structure

```
microservice-health-monitor/
├── services/
│   ├── user-service/          # User management API
│   ├── order-service/         # Order management API
│   └── notification-service/  # Notification dispatch API
├── dashboard/                 # Real-time health dashboard
│   ├── index.html
│   ├── style.css
│   └── app.js
├── terraform/                 # Infrastructure as Code
│   ├── main.tf               # Root module
│   ├── variables.tf
│   ├── outputs.tf
│   ├── backend.tf            # Remote state config
│   └── modules/
│       ├── networking/        # VPC, subnets, SGs
│       ├── ecr/               # Container registries
│       ├── ecs/               # Cluster, tasks, services
│       ├── alb/               # Load balancer + routing
│       ├── monitoring/        # CloudWatch + SNS
│       └── frontend/          # S3 + CloudFront
├── .github/workflows/
│   ├── ci.yml                 # PR: test, lint, validate
│   └── deploy.yml             # Main: build, push, deploy
├── docker-compose.yml         # Local development
└── README.md
```

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Python 3.12+](https://www.python.org/downloads/)
- [Terraform 1.5+](https://developer.hashicorp.com/terraform/downloads) (for AWS deployment)
- [AWS CLI v2](https://aws.amazon.com/cli/) (for AWS deployment)

### Local Development (No AWS needed)

```bash
# Clone the repository
git clone https://github.com/<your-username>/microservice-health-monitor.git
cd microservice-health-monitor

# Start all services with Docker Compose
docker-compose up -d --build

# Verify services are running
curl http://localhost:5001/api/users/health
curl http://localhost:5002/api/orders/health
curl http://localhost:5003/api/notifications/health

# Open the dashboard
# Open dashboard/index.html in your browser
# (Set CONFIG.demoMode = false in app.js to poll real services)
```

### Run Tests

```bash
# Test each service individually
cd services/user-service
pip install -r requirements.txt
pytest tests/ -v

cd ../order-service
pip install -r requirements.txt
pytest tests/ -v

cd ../notification-service
pip install -r requirements.txt
pytest tests/ -v
```

## AWS Deployment

### 1. Configure AWS Credentials

```bash
aws configure
# Or set environment variables:
# export AWS_ACCESS_KEY_ID=...
# export AWS_SECRET_ACCESS_KEY=...
# export AWS_DEFAULT_REGION=ap-south-1
```

### 2. Deploy Infrastructure

```bash
cd terraform

# Create your tfvars file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### 3. Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Build and push each service
for service in user-service order-service notification-service; do
    docker build -t mshealth/$service ./services/$service
    docker tag mshealth/$service:latest <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/mshealth/$service:latest
    docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/mshealth/$service:latest
done
```

### 4. Deploy Dashboard

```bash
aws s3 sync dashboard/ s3://$(terraform output -raw s3_dashboard_bucket)/ --delete
aws cloudfront create-invalidation --distribution-id $(terraform output -raw cloudfront_distribution_id) --paths "/*"
```

### 5. Set Up CI/CD (GitHub Actions)

1. Create an OIDC identity provider in AWS IAM
2. Create an IAM role for GitHub Actions with the required permissions
3. Add these GitHub secrets:
   - `AWS_ROLE_ARN`: ARN of the OIDC role
   - `DASHBOARD_BUCKET`: S3 bucket name (from Terraform output)
   - `CLOUDFRONT_DIST_ID`: CloudFront distribution ID (from Terraform output)

## API Endpoints

### User Service (`:5001`)
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/users/health` | Health check |
| `GET` | `/api/users` | List all users |
| `GET` | `/api/users/:id` | Get user by ID |
| `POST` | `/api/users` | Create a new user |

### Order Service (`:5002`)
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/orders/health` | Health check |
| `GET` | `/api/orders` | List all orders |
| `GET` | `/api/orders/:id` | Get order by ID |
| `POST` | `/api/orders` | Create a new order |
| `PATCH` | `/api/orders/:id/status` | Update order status |

### Notification Service (`:5003`)
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/notifications/health` | Health check |
| `GET` | `/api/notifications` | List notifications |
| `POST` | `/api/notifications/send` | Send a notification |
| `GET` | `/api/notifications/stats` | Notification stats |

## CI/CD Pipeline

### PR Pipeline (`ci.yml`)
```
Trigger: Pull Request to main
├── Test Services (parallel matrix)
│   ├── user-service: lint + pytest
│   ├── order-service: lint + pytest
│   └── notification-service: lint + pytest
├── Docker Build (validate Dockerfiles)
└── Terraform Validate (fmt + validate)
```

### Deploy Pipeline (`deploy.yml`)
```
Trigger: Push to main
├── Detect Changes (path-based filtering)
├── Run Tests (all services)
├── Build & Push to ECR (only changed services)
├── Deploy to ECS (force new deployment + stability wait)
└── Deploy Dashboard (S3 sync + CloudFront invalidation)
```

## Cost Estimation

| Resource | Monthly Cost (approx.) |
|----------|----------------------|
| ECS Fargate (3 tasks, 0.25 vCPU / 0.5 GB) | ~$30 |
| ALB | ~$22 |
| NAT Gateway | ~$35 |
| CloudWatch | ~$3 |
| S3 + CloudFront | ~$1 |
| ECR | ~$1 |
| **Total** | **~$92/mo** |

> ** Tip**: For demo purposes, deploy → screenshot → tear down with `terraform destroy`. Total cost: a few dollars.

## Teardown

```bash
cd terraform
terraform destroy
```

## License

This project is open source and available under the [MIT License](LICENSE).

---
