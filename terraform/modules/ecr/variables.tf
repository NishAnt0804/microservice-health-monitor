variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "service_names" {
  description = "List of microservice names"
  type        = list(string)
}
