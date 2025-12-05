terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {}

# Define the Image
resource "docker_image" "lazarus_app" {
  name         = "lazarus_enterprise:latest"
  keep_locally = false
}

# Define the Container
resource "docker_container" "lazarus_api" {
  image = docker_image.lazarus_app.image_id
  name  = "lazarus_api_prod"
  
  ports {
    internal = 80
    external = 8000
  }
  
  env = [
    "environment=production",
    "REDIS_URL=redis://redis:6379/0"
  ]
  
  # Health Check (Infrastructure Level)
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:80/health"]
    interval = "30s"
    retries  = 3
  }
}

# Note: In a real cloud scenario (AWS/Azure), this file would define:
# - VPCs, Subnets, Security Groups
# - ECS Clusters or Kubernetes Nodes
# - RDS Databases
# - Redis ElastiCache
