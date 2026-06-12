# ---------------------------------------------------------------------------
# Monitoring Module — CloudWatch Alarms, Dashboard, SNS Alerts
# ---------------------------------------------------------------------------

# --- SNS Topic for Alerts ---
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# --- CloudWatch Alarms: EC2 CPU Utilization ---
resource "aws_cloudwatch_metric_alarm" "ec2_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ec2-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "High CPU utilization for Docker Host EC2"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = var.ec2_instance_id
  }

  tags = {
    Environment = var.environment
  }
}

# --- CloudWatch Alarms: EC2 Status Check Failed ---
resource "aws_cloudwatch_metric_alarm" "ec2_status_failed" {
  alarm_name          = "${var.project_name}-${var.environment}-ec2-status-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "EC2 Instance or System Status Check Failed"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = var.ec2_instance_id
  }

  tags = {
    Environment = var.environment
  }
}

# --- CloudWatch Dashboard ---
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = concat(
      # Title widget
      [
        {
          type   = "text"
          x      = 0
          y      = 0
          width  = 24
          height = 1
          properties = {
            markdown = "# 🏥 ${var.project_name} — ${var.environment} Environment (Free Tier EC2)"
          }
        }
      ],
      # EC2 CPU
      [
        {
          type   = "metric"
          x      = 0
          y      = 1
          width  = 12
          height = 6
          properties = {
            title   = "Docker Host CPU %"
            metrics = [["AWS/EC2", "CPUUtilization", "InstanceId", var.ec2_instance_id]]
            period  = 300
            stat    = "Average"
            region  = var.aws_region
            view    = "timeSeries"
          }
        }
      ],
      # EC2 Network In/Out
      [
        {
          type   = "metric"
          x      = 12
          y      = 1
          width  = 12
          height = 6
          properties = {
            title   = "Docker Host Network (Bytes)"
            metrics = [
              ["AWS/EC2", "NetworkIn", "InstanceId", var.ec2_instance_id],
              ["AWS/EC2", "NetworkOut", "InstanceId", var.ec2_instance_id]
            ]
            period  = 300
            stat    = "Sum"
            region  = var.aws_region
            view    = "timeSeries"
          }
        }
      ]
    )
  })
}
