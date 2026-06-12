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
│  │  Lint   │──▶│  Test    │──▶│  Build   │──▶│ Deploy via SSM  │  │
│  └─────────┘   └──────────┘   └──────────┘   └─────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │ (OIDC Authentication)
                                        ▼
┌─────────────────────────── AWS Cloud ──────────────────────────────┐
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  VPC Public Subnet                                          │   │
│  │  ┌────────────────────────────────────────────────────────┐ │   │
│  │  │  EC2 t3.micro (Docker Host)                            │ │   │
│  │  │                                                        │ │   │
│  │  │  ┌────────────┐   ┌──────────┐ ┌──────────┐ ┌────────┐ │ │   │
│  │  │  │  NGINX     │──▶│ user-svc │ │ order-svc│ │notif-svc│ │ │   │
│  │  │  │  (:80)     │   └──────────┘ └──────────┘ └────────┘ │ │   │
│  │  │  └────────────┘                                        │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────┐  ┌────────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │  ECR   │  │ CloudWatch │  │    SNS    │  │  S3 + CloudFront │   │
│  │ Images │  │  EC2 Alarms│  │  Alerts   │  │  Dashboard       │   │
│  └────────┘  └────────────┘  └───────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer              | Technology                                    |
|--------------------|-----------------------------------------------|
| **Backend**        | Python 3.12, Flask, Gunicorn                  |
| **Containers**     | Docker (multi-stage builds)                   |
| **Orchestration**  | Docker Compose                                |
| **Compute**        | AWS EC2 (t3.micro, Free Tier)                 |
| **Registry**       | AWS ECR (image scanning, lifecycle policies)  |
| **Load Balancing** | NGINX Reverse Proxy                           |
| **Networking**     | VPC, Public Subnet, Security Groups           |
| **Monitoring**     | CloudWatch Logs, Alarms, Dashboard            |
| **Alerting**       | AWS SNS (email notifications)                 |
| **IaC**            | Terraform (6 modular modules)                 |
| **CI/CD**          | GitHub Actions (OIDC auth, SSM Deploy)        |
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
│       ├── ec2/               # Docker host instance
│       ├── monitoring/        # CloudWatch + SNS
│       └── frontend/          # S3 + CloudFront
├── .github/workflows/
│   ├── ci.yml                 # PR: test, lint, validate
│   └── deploy.yml             # Main: build, push, deploy via SSM
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
git clone https://github.com/<NishAnt0804>/microservice-health-monitor.git
cd microservice-health-monitor

# Start all services with Docker Compose
docker-compose up -d --build

# Verify services are running
curl http://localhost:5001/api/users/health
curl http://localhost:5002/api/orders/health
curl http://localhost:5003/api/notifications/health
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
# Set Default Region to ap-south-1
# Set Output format to json
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

### 3. Push Docker Images (Manual First Run)

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
   - `EC2_INSTANCE_ID`: Your EC2 Instance ID (from Terraform output)

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
├── Deploy to EC2 via AWS SSM (No SSH keys!)
└── Deploy Dashboard (S3 sync + CloudFront invalidation)
```

## Cost Estimation

| Resource | Monthly Cost (approx.) |
|----------|----------------------|
| EC2 `t3.micro` | **$0.00** (First 750 hrs/month) |
| VPC, Subnets, IGW | **$0.00** |
| CloudWatch | **$0.00** (First 10 alarms / 1M requests free) |
| S3 + CloudFront | **$0.00** (Free tier limits) |
| ECR | **$0.00** (First 500MB free) |
| **Total** | **$0.00/mo** |


## Teardown

```bash
cd terraform
terraform destroy
```

## License

This project is open source and available under the [MIT License](LICENSE).
