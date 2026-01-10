# Airflow Remote Server Setup Guide

Complete guide for deploying Airflow on a remote server (Linode, AWS, etc.) using Docker Compose.

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 4GB (8GB recommended)
- **CPU**: 2+ cores
- **Disk**: 20GB+ free space
- **Docker**: Docker Engine + Docker Compose installed

### Install Docker (if needed)

```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose (if not included)
sudo apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

## Step 1: Pre-Configuration (IMPORTANT - Do Before Starting)

These settings prevent common warnings and errors.

### 1.1 Create/Edit `.env` File

**CRITICAL**: Set `AIRFLOW_UID` to match your user ID to avoid permission issues and root user warnings.

```bash
# Find your user ID
echo $UID

# Create .env file with proper settings
cat > .env << 'EOF'
# Airflow User ID (prevents root user warning)
AIRFLOW_UID=1000

# Admin credentials
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=your_secure_password_here

# Disable example DAGs (cleaner UI)
AIRFLOW__CORE__LOAD_EXAMPLES=false

# Database configuration
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# Redis configuration
REDIS_PASSWORD=

# Executor
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
EOF
```

### 1.2 Firewall Configuration

Open required ports before starting Airflow:

```bash
# Web UI port
sudo ufw allow 8080/tcp

# Optional: Flower monitoring UI
sudo ufw allow 5555/tcp

# Optional: If using SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 1.3 Download Official docker-compose.yaml

```bash
# Create airflow directory
mkdir -p ~/airflow
cd ~/airflow

# Download official docker-compose file
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'

# Create required directories
mkdir -p ./dags ./logs ./plugins ./config
```

## Step 2: Initialize Airflow (First Time Only)

```bash
cd ~/airflow

# Initialize the database and create admin user
docker compose up airflow-init

# Wait for "airflow-init_1 exited with code 0"
# This means initialization was successful
```

**Expected Output:**
```
User "admin" created with role "Admin"
...
airflow-init_1 exited with code 0
```

## Step 3: Start All Services

```bash
# Start all Airflow services in background
docker compose up -d

# Wait 30-60 seconds for all services to start
sleep 60

# Check all services are healthy
docker compose ps
```

**Expected Services:**
```
airflow-apiserver       Up (healthy)   0.0.0.0:8080->8080/tcp
airflow-scheduler       Up (healthy)
airflow-worker          Up (healthy)
airflow-dag-processor   Up (healthy)
airflow-triggerer       Up (healthy)
postgres                Up (healthy)
redis                   Up (healthy)
```

## Step 4: Verify Access

### Web UI

```bash
# Get your server's public IP
curl ifconfig.me

# Access in browser:
# http://YOUR_SERVER_IP:8080

# Login with credentials from .env:
# Username: admin
# Password: your_secure_password_here
```

### Command Line

```bash
# Test Airflow CLI
docker compose run airflow-cli airflow version

# List DAGs
docker compose run airflow-cli airflow dags list

# Check database connection
docker compose run airflow-cli airflow db check
```

## Common Warnings and How to Fix Them

### Warning: "No services to build"

**What it means**: Images are already downloaded/built
**Action**: Ignore - this is normal

### Warning: "Found orphan containers"

**What it means**: Leftover containers from previous runs
**Fix:**
```bash
docker compose down --remove-orphans
docker compose up -d
```

### Warning: "Container is run as root user"

**What it means**: AIRFLOW_UID not set
**Fix:**
```bash
# Add to .env file
echo "AIRFLOW_UID=$(id -u)" >> .env

# Restart services
docker compose down
docker compose up -d
```

### Deprecation Warnings (kubernetes_executor, etc.)

**What it means**: Configuration format changes in future versions
**Action**: Safe to ignore unless you're using Kubernetes executor

## Troubleshooting

### Services Won't Start

```bash
# Check logs for specific service
docker compose logs airflow-scheduler
docker compose logs airflow-apiserver
docker compose logs postgres

# Check all logs
docker compose logs -f

# Check disk space
df -h

# Check memory
free -h
```

### Can't Access Web UI

```bash
# Check if port is listening
sudo netstat -tulpn | grep 8080

# Check firewall
sudo ufw status

# Check service status
docker compose ps airflow-apiserver

# Restart apiserver
docker compose restart airflow-apiserver
```

### Database Connection Errors

```bash
# Check postgres is healthy
docker compose ps postgres

# View postgres logs
docker compose logs postgres

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

### Out of Memory Errors

```bash
# Check memory usage
docker stats

# If low memory, stop non-essential services:
docker compose stop airflow-triggerer  # If not using triggers
docker compose stop flower             # If not using monitoring
```

## Maintenance Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f airflow-scheduler

# Last 100 lines
docker compose logs --tail=100 airflow-apiserver
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart airflow-scheduler

# Full restart (down + up)
docker compose down
docker compose up -d
```

### Update Airflow

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose down
docker compose up -d
```

### Backup and Restore

```bash
# Backup database
docker compose exec postgres pg_dump -U airflow airflow > airflow_backup_$(date +%Y%m%d).sql

# Restore database
cat airflow_backup_20260110.sql | docker compose exec -T postgres psql -U airflow airflow
```

### Clean Up

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove everything including images
docker compose down -v --rmi all

# Remove orphan containers
docker compose down --remove-orphans
```

## Security Best Practices

### 1. Change Default Passwords

Edit `.env`:
```bash
_AIRFLOW_WWW_USER_PASSWORD=strong_random_password
POSTGRES_PASSWORD=another_strong_password
```

Then restart:
```bash
docker compose down
docker compose up -d
```

### 2. Enable HTTPS (Production)

Use a reverse proxy like Nginx:

```bash
# Install Nginx
sudo apt-get install nginx

# Configure SSL with Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d airflow.yourdomain.com
```

### 3. Restrict Access

```bash
# Only allow specific IPs to access port 8080
sudo ufw delete allow 8080/tcp
sudo ufw allow from YOUR_IP to any port 8080
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
docker compose pull
docker compose up -d
```

## Performance Tuning

### Adjust Worker Concurrency

Edit `docker-compose.yaml` or set in `.env`:

```bash
AIRFLOW__CELERY__WORKER_CONCURRENCY=16  # Adjust based on CPU cores
```

### Increase Parallelism

```bash
AIRFLOW__CORE__PARALLELISM=32
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=16
```

### Reduce Memory Usage

```bash
# Disable Flower if not needed
docker compose stop flower

# Reduce worker concurrency
AIRFLOW__CELERY__WORKER_CONCURRENCY=4
```

## Monitoring

### Check Service Health

```bash
# Quick status
docker compose ps

# Detailed stats
docker stats

# Check specific service health
curl http://localhost:8080/health
```

### Enable Flower (Celery Monitoring)

Flower is included but may not be running by default. Check `docker-compose.yaml` for the flower service.

Access at: `http://YOUR_SERVER_IP:5555`

## Quick Reference Commands

```bash
# Start
cd ~/airflow && docker compose up -d

# Stop
cd ~/airflow && docker compose down

# Restart
cd ~/airflow && docker compose restart

# Logs
cd ~/airflow && docker compose logs -f

# Status
cd ~/airflow && docker compose ps

# CLI
cd ~/airflow && docker compose run airflow-cli airflow [command]

# Clean restart
cd ~/airflow && docker compose down && docker compose up -d
```

## Resources

- **Official Docs**: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- **Docker Hub**: https://hub.docker.com/r/apache/airflow
- **Community**: https://airflow.apache.org/community/

## Checklist for Fresh Setup

- [ ] Server has 4GB+ RAM
- [ ] Docker and Docker Compose installed
- [ ] Created `.env` file with `AIRFLOW_UID`
- [ ] Opened firewall port 8080
- [ ] Created dags/logs/plugins/config directories
- [ ] Downloaded docker-compose.yaml
- [ ] Ran `docker compose up airflow-init`
- [ ] Ran `docker compose up -d`
- [ ] Waited 60 seconds for services to start
- [ ] Verified all services healthy: `docker compose ps`
- [ ] Accessed Web UI at http://SERVER_IP:8080
- [ ] Changed default admin password
- [ ] (Optional) Set up SSL with reverse proxy
- [ ] (Optional) Configured backups
