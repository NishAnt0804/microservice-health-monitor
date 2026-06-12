# ---------------------------------------------------------------------------
# EC2 Module — Single Free Tier Instance running Docker Compose + NGINX
# ---------------------------------------------------------------------------

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# --- Security Group for EC2 ---
resource "aws_security_group" "ec2" {
  name_prefix = "${var.project_name}-${var.environment}-ec2-"
  description = "Security group for EC2 Docker Host"
  vpc_id      = var.vpc_id

  # Allow HTTP (for APIs and Dashboard)
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-sg"
    Environment = var.environment
  }
}

# --- IAM Role for EC2 (SSM, ECR, CloudWatch) ---
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Attach SSM Core policy (allows Systems Manager connection)
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach policy to allow pulling from ECR and pushing logs
resource "aws_iam_role_policy" "ec2_custom_policy" {
  name = "ecr-cloudwatch-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# --- EC2 Instance ---
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # No SSH Key needed because we use SSM!

  user_data = <<-EOF
    #!/bin/bash
    # Update and install Docker
    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ssm-user

    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Create app directory
    mkdir -p /app/nginx
    cd /app

    # Create NGINX config (Replacing ALB functionality)
    cat > nginx/nginx.conf << 'NGINX_CONF'
    events {
        worker_connections 1024;
    }
    http {
        server {
            listen 80;

            # CORS headers
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, PATCH, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'X-Requested-With,Accept,Content-Type, Origin' always;

            location /api/users/ {
                proxy_pass http://user-service:5001/api/users/;
                proxy_set_header Host \$host;
                proxy_set_header X-Real-IP \$remote_addr;
            }

            location /api/orders/ {
                proxy_pass http://order-service:5002/api/orders/;
                proxy_set_header Host \$host;
                proxy_set_header X-Real-IP \$remote_addr;
            }

            location /api/notifications/ {
                proxy_pass http://notification-service:5003/api/notifications/;
                proxy_set_header Host \$host;
                proxy_set_header X-Real-IP \$remote_addr;
            }

            # Health check for NGINX itself
            location /health {
                return 200 'OK';
                add_header Content-Type text/plain;
            }
        }
    }
    NGINX_CONF

    # Create production docker-compose.yml
    cat > docker-compose.prod.yml << 'COMPOSE'
    version: '3.9'
    services:
      user-service:
        image: ${var.ecr_urls["user-service"]}:latest
        environment:
          - PORT=5001
        restart: always

      order-service:
        image: ${var.ecr_urls["order-service"]}:latest
        environment:
          - PORT=5002
        restart: always

      notification-service:
        image: ${var.ecr_urls["notification-service"]}:latest
        environment:
          - PORT=5003
        restart: always

      nginx:
        image: nginx:alpine
        ports:
          - "80:80"
        volumes:
          - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
        depends_on:
          - user-service
          - order-service
          - notification-service
        restart: always
    COMPOSE

    # Set permissions
    chown -R ssm-user:ssm-user /app

    # We don't start it here because images aren't pushed yet.
    # GitHub Actions will start it after pushing images.
  EOF

  tags = {
    Name        = "${var.project_name}-${var.environment}-docker-host"
    Environment = var.environment
  }
}
