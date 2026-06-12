# ---------------------------------------------------------------------------
# Terraform Backend Configuration
# ---------------------------------------------------------------------------
# Uncomment the block below to use S3 remote state.
# You'll need to create the S3 bucket and DynamoDB table first:
#
#   aws s3api create-bucket --bucket mshealth-terraform-state-<ACCOUNT_ID> \
#       --region ap-south-1 --create-bucket-configuration LocationConstraint=ap-south-1
#
#   aws dynamodb create-table --table-name mshealth-terraform-locks \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST --region ap-south-1

# terraform {
#   backend "s3" {
#     bucket         = "mshealth-terraform-state-<ACCOUNT_ID>"
#     key            = "microservice-health-monitor/terraform.tfstate"
#     region         = "ap-south-1"
#     dynamodb_table = "mshealth-terraform-locks"
#     encrypt        = true
#   }
# }
