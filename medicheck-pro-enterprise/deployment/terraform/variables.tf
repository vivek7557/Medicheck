# AWS Region
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

# Availability Zones
variable "availability_zones" {
  description = "List of availability zones for the VPC"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

# EKS Cluster
variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "medicheck-cluster"
}

# EKS Node Group
variable "instance_types" {
  description = "EC2 instance types for the EKS nodes"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge"]
}

variable "node_min_size" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 10
}

variable "node_desired_size" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 3
}

# Database
variable "db_instance_class" {
  description = "Instance class for RDS instance"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "medicheck_user"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

# Container Registry
variable "ecr_repository_name" {
  description = "Name for the ECR repository"
  type        = string
  default     = "medicheck-pro-enterprise"
}

# S3 Bucket
variable "s3_bucket_name" {
  description = "Name for the S3 bucket"
  type        = string
  default     = "medicheck-pro-enterprise-bucket"
}