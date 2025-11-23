# MediCheck Pro Enterprise Deployment Guide

## Overview

This guide provides instructions for deploying MediCheck Pro Enterprise in various environments, from development to production.

## Prerequisites

### System Requirements

- **CPU**: 4 cores or more recommended
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 50GB available space
- **OS**: Linux (Ubuntu 20.04+ or CentOS 7+), macOS, or Windows with WSL2
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Python**: Version 3.9 or higher

### Software Dependencies

- Git
- Docker and Docker Compose
- Python 3.9+
- pip
- Terraform (for cloud deployments)
- kubectl (for Kubernetes deployments)
- AWS CLI (for AWS deployments)

## Development Deployment

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/your-org/medicheck-pro-enterprise.git
cd medicheck-pro-enterprise
```

2. Create a `.env` file with your environment variables:
```bash
cp .env.example .env
```

3. Edit the `.env` file to include your API keys and database credentials:
```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://medicheck_user:password@postgres:5432/medicheck
DB_PASSWORD=your_db_password
```

4. Build and start the services:
```bash
cd deployment/docker
docker-compose up --build
```

5. Access the application at `http://localhost:8501`

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY=your_api_key
export DATABASE_URL=postgresql://localhost:5432/medicheck
```

3. Run the application:
```bash
cd app
streamlit run main.py
```

## Production Deployment

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (EKS, AKS, GKE, or self-managed)
- kubectl configured to connect to your cluster
- Helm (optional, for easier management)

#### Steps

1. Apply the Kubernetes manifests:
```bash
kubectl apply -f deployment/kubernetes/
```

2. Create secrets for sensitive data:
```bash
kubectl create secret generic medicheck-secrets \
  --from-literal=database_url="postgresql://user:pass@host:port/db" \
  --from-literal=openai_api_key="your_api_key"
```

3. Verify deployment:
```bash
kubectl get pods
kubectl get services
```

4. Access the application via the LoadBalancer service:
```bash
kubectl get service medicheck-pro-enterprise-service
```

### AWS Deployment with Terraform

#### Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured
- Terraform installed

#### Steps

1. Navigate to the Terraform directory:
```bash
cd deployment/terraform
```

2. Initialize Terraform:
```bash
terraform init
```

3. Create a `terraform.tfvars` file with your variables:
```bash
cluster_name = "medicheck-prod"
db_password = "your_secure_db_password"
```

4. Review the execution plan:
```bash
terraform plan
```

5. Apply the configuration:
```bash
terraform apply
```

6. Once deployment is complete, update your kubeconfig to connect to the EKS cluster:
```bash
aws eks --region $(terraform output -raw aws_region) update-kubeconfig --name $(terraform output -raw cluster_name)
```

7. Deploy the application manifests to the cluster:
```bash
kubectl apply -f ../kubernetes/
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENV` | Environment (development, staging, production) | Yes | development |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `DATABASE_URL` | Database connection string | Yes | - |
| `REDIS_URL` | Redis connection string | No | redis://localhost:6379 |
| `LOG_LEVEL` | Logging level | No | INFO |
| `MAX_WORKERS` | Maximum number of worker processes | No | 4 |
| `ENABLE_TRACING` | Enable distributed tracing | No | false |
| `TRACING_ENDPOINT` | Tracing collector endpoint | No | http://localhost:4317 |

### Database Configuration

The application supports PostgreSQL with pgvector extension for vector storage. For production deployments:

1. Ensure your PostgreSQL instance has the pgvector extension installed
2. Configure connection pooling settings appropriately
3. Set up regular backups
4. Enable encryption in transit and at rest

### Security Configuration

#### HTTPS/SSL

For production deployments, ensure SSL termination is properly configured:

1. Use a reverse proxy (nginx, traefik) with SSL termination
2. Configure certificate management (Let's Encrypt, AWS ACM)
3. Implement HSTS headers

#### Authentication

The system supports multiple authentication methods:

1. **API Key Authentication**: For service-to-service communication
2. **OAuth 2.0**: For user authentication
3. **JWT Tokens**: For session management

### Scaling Configuration

#### Horizontal Pod Autoscaling (HPA)

The Kubernetes deployment includes HPA configuration:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: medicheck-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: medicheck-pro-enterprise
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Database Scaling

For high-traffic deployments:

1. Implement read replicas for database queries
2. Use connection pooling
3. Configure appropriate indexing
4. Monitor query performance

## Monitoring and Logging

### Application Metrics

The application exposes metrics at `/metrics` endpoint in Prometheus format:

- `http_requests_total`: Total HTTP requests by status code and method
- `agent_execution_duration_seconds`: Duration of agent executions
- `database_connections`: Current database connections
- `active_sessions`: Number of active user sessions

### Health Checks

The application provides health check endpoints:

- `/health`: Overall system health
- `/ready`: Readiness for traffic
- `/live`: Liveness probe

### Log Management

Logs are structured in JSON format and include:

- Timestamp
- Log level
- Service name
- Trace ID (for distributed tracing)
- Request context
- Error details (if applicable)

## Backup and Recovery

### Database Backup

Regular database backups are essential:

```bash
# PostgreSQL backup example
pg_dump -h hostname -U username -d medicheck > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Application Backup

For containerized deployments, ensure:

1. Persistent volumes are backed up
2. Configuration files are versioned
3. Secrets are securely stored
4. Container images are properly tagged

## Troubleshooting

### Common Issues

#### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check that the database service is running
- Ensure proper network connectivity
- Confirm credentials are valid

#### API Key Issues

- Verify API key format and validity
- Check rate limits
- Ensure proper environment variable configuration

#### Performance Issues

- Monitor resource utilization
- Check for database query performance
- Review agent execution times
- Verify proper scaling configuration

### Diagnostic Commands

#### Docker Compose
```bash
# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Execute commands in containers
docker-compose exec medicheck-pro bash
```

#### Kubernetes
```bash
# View pod logs
kubectl logs -f deployment/medicheck-pro-enterprise

# Check resource usage
kubectl top pods

# Execute commands in pods
kubectl exec -it deployment/medicheck-pro-enterprise -- bash
```

## Security Best Practices

### Data Protection

1. Encrypt all sensitive data in transit and at rest
2. Implement proper access controls
3. Regular security audits
4. Data anonymization for non-production environments

### Network Security

1. Use private networks when possible
2. Implement proper firewall rules
3. Use VPN for administrative access
4. Regular network security assessments

### Compliance

The system is designed to support HIPAA compliance:

1. Access logging and audit trails
2. Data encryption
3. Role-based access control
4. Regular compliance reporting