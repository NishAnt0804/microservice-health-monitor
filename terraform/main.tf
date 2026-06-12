# ---------------------------------------------------------------------------
# Microservice Health Monitor — Root Terraform Configuration
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = { Project = var.project_name, Environment = var.environment, ManagedBy = "terraform" }
  }
}

data "aws_caller_identity" "current" {}

locals {
  service_names = ["user-service", "order-service", "notification-service"]
}

# --- Module: Networking ---
module "networking" {
  source = "./modules/networking"
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

# --- Module: ECR ---
module "ecr" {
  source        = "./modules/ecr"
  project_name  = var.project_name
  environment   = var.environment
  service_names = local.service_names
}

# --- Module: EC2 Docker Host ---
module "ec2" {
  source        = "./modules/ec2"
  project_name  = var.project_name
  environment   = var.environment
  vpc_id        = module.networking.vpc_id
  subnet_id     = module.networking.public_subnet_ids[0]
  instance_type = "t3.micro"
  ecr_urls      = module.ecr.repository_urls
}

# --- Module: Monitoring ---
module "monitoring" {
  source          = "./modules/monitoring"
  project_name    = var.project_name
  environment     = var.environment
  aws_region      = var.aws_region
  alert_email     = var.alert_email
  ec2_instance_id = module.ec2.instance_id
}

# --- Module: Frontend (Dashboard) ---
module "frontend" {
  source         = "./modules/frontend"
  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
}
