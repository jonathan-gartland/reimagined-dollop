# Airflow DAG Deployment Guide

How to deploy DAGs from this repository to a remote Airflow server.

## Overview

This repository contains Airflow DAGs that need to be deployed to your Airflow server. There are several approaches, each with pros and cons.

## Recommended: Git Clone + Symlinks

**Best for**: Ongoing development with frequent updates

### Setup (One-time)

```bash
# On the remote server (SSH as root)
cd ~

# Clone the repository
git clone git@github.com:jonathan-gartland/reimagined-dollop.git liquor_app
# Or use HTTPS: git clone https://github.com/jonathan-gartland/reimagined-dollop.git liquor_app

# Create symlinks in Airflow directories
cd ~/airflow

# Symlink DAG files
ln -sf ~/liquor_app/dags/whiskey_sync_dag.py dags/whiskey_sync_dag.py
ln -sf ~/liquor_app/dags/README.md dags/README.md

# Symlink scripts directory
ln -sf ~/liquor_app/scripts scripts

# Restart Airflow to pick up changes
docker compose restart airflow-scheduler airflow-dag-processor
```

### Update DAGs (whenever you make changes)

```bash
# On the remote server
cd ~/liquor_app
git pull

# Restart scheduler to pick up changes
cd ~/airflow
docker compose restart airflow-scheduler airflow-dag-processor
```

### Using the Deploy Script (from your local machine)

```bash
# From your local machine
./deploy-to-remote.sh YOUR_LINODE_IP

# Example
./deploy-to-remote.sh 97.107.138.118
```

**Pros:**
- ✅ Single source of truth (Git)
- ✅ Easy to update (just `git pull`)
- ✅ Full version history
- ✅ Changes immediately reflected
- ✅ Can roll back easily (`git checkout`)

**Cons:**
- ❌ Requires Git on server
- ❌ Requires SSH access or GitHub credentials

## Alternative 1: Direct Copy

**Best for**: Simple deployments, no ongoing development

```bash
# From your local machine
scp dags/whiskey_sync_dag.py root@YOUR_LINODE_IP:~/airflow/dags/
scp -r scripts/ root@YOUR_LINODE_IP:~/airflow/

# Restart scheduler
ssh root@YOUR_LINODE_IP "cd ~/airflow && docker compose restart airflow-scheduler"
```

**Pros:**
- ✅ Simple and straightforward
- ✅ No Git needed on server

**Cons:**
- ❌ Manual process for updates
- ❌ No version history on server
- ❌ Need to copy multiple files/directories

## Alternative 2: Volume Mount Entire Repo

**Best for**: Development environment, frequent iteration

Modify the server's `docker-compose.yaml` to mount your repo:

```yaml
# In docker-compose.yaml on server
volumes:
  - ~/liquor_app/dags:/opt/airflow/dags
  - ~/liquor_app/scripts:/opt/airflow/scripts
  - ~/liquor_app/sql:/opt/airflow/sql
```

Then just `git pull` to update:

```bash
cd ~/liquor_app && git pull
# Airflow auto-detects changes (may take 30-60 seconds)
```

**Pros:**
- ✅ Automatic DAG detection
- ✅ No restart needed (usually)
- ✅ Clean separation

**Cons:**
- ❌ Requires modifying docker-compose.yaml
- ❌ Entire repo on server (may include unnecessary files)

## Alternative 3: CI/CD with GitHub Actions

**Best for**: Production environments, automated deployments

Create `.github/workflows/deploy-airflow.yml`:

```yaml
name: Deploy to Airflow

on:
  push:
    branches: [main]
    paths:
      - 'dags/**'
      - 'scripts/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Linode
        env:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          SERVER_IP: ${{ secrets.SERVER_IP }}
        run: |
          mkdir -p ~/.ssh
          echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan $SERVER_IP >> ~/.ssh/known_hosts

          # Deploy files
          scp -r dags/ root@$SERVER_IP:~/airflow/
          scp -r scripts/ root@$SERVER_IP:~/airflow/

          # Restart scheduler
          ssh root@$SERVER_IP "cd ~/airflow && docker compose restart airflow-scheduler"
```

**Pros:**
- ✅ Fully automated
- ✅ Deploys on every push to main
- ✅ Professional workflow

**Cons:**
- ❌ Requires GitHub Actions setup
- ❌ Need to store SSH keys in GitHub secrets
- ❌ More complex initial setup

## DAG Update Detection

Airflow checks for DAG changes every 30-60 seconds by default. You can:

### Force Immediate Detection

```bash
# Restart scheduler and dag processor
docker compose restart airflow-scheduler airflow-dag-processor

# Or just the dag processor (faster)
docker compose restart airflow-dag-processor
```

### Adjust Detection Interval

In `airflow/.env` or docker-compose environment:

```bash
# Check for DAG changes every 10 seconds (faster, more CPU)
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=10

# Default is 300 seconds (5 minutes)
```

## Verifying Deployment

### 1. Check Files Exist

```bash
# On the server
ls -la ~/airflow/dags/
ls -la ~/airflow/scripts/

# Should see your DAG files
```

### 2. Check Airflow Logs

```bash
# On the server
docker compose logs -f airflow-dag-processor

# Look for:
# "Found DAG: whiskey_data_sync"
# Or errors if DAG has issues
```

### 3. Check Web UI

- Open http://YOUR_LINODE_IP:8080
- Go to "DAGs" page
- Look for `whiskey_data_sync`
- Check for any import errors (red banner)

### 4. Test DAG Parsing

```bash
# On the server
docker compose run airflow-cli airflow dags list-import-errors

# Should return empty if no errors
```

## Troubleshooting

### DAG Not Appearing in UI

```bash
# 1. Check file exists
ls -la ~/airflow/dags/whiskey_sync_dag.py

# 2. Check for Python errors
docker compose run airflow-cli airflow dags list-import-errors

# 3. Check scheduler logs
docker compose logs airflow-dag-processor | grep -i error

# 4. Manually trigger DAG parsing
docker compose restart airflow-dag-processor
```

### DAG Has Import Errors

```bash
# Check what's wrong
docker compose run airflow-cli python /opt/airflow/dags/whiskey_sync_dag.py

# Check logs
docker compose logs airflow-dag-processor
```

### Dependencies Missing

If your DAG needs packages not in the base Airflow image:

```bash
# Option 1: Install in running container (temporary)
docker compose exec airflow-worker pip install package-name

# Option 2: Add to docker-compose.yaml (permanent)
# In environment section:
_PIP_ADDITIONAL_REQUIREMENTS: python-dotenv psycopg2-binary

# Then restart
docker compose down && docker compose up -d
```

## Security Considerations

### Use Deploy Keys for Git

Instead of your personal SSH key:

1. Generate a deploy key on the server:
   ```bash
   ssh-keygen -t ed25519 -C "airflow-deploy-key" -f ~/.ssh/airflow_deploy
   ```

2. Add the public key to GitHub:
   - Settings → Deploy Keys → Add deploy key
   - Paste contents of `~/.ssh/airflow_deploy.pub`
   - ✅ Allow write access (only if pushing from server)

3. Configure Git to use it:
   ```bash
   git clone git@github.com:jonathan-gartland/reimagined-dollop.git liquor_app
   # Or update existing:
   cd ~/liquor_app
   git remote set-url origin git@github.com:jonathan-gartland/reimagined-dollop.git
   ```

### Don't Store Secrets in DAG Files

Use Airflow Connections or Variables instead:

```python
# Bad - hardcoded
DB_PASSWORD = "mypassword"

# Good - from Airflow Variable
from airflow.models import Variable
DB_PASSWORD = Variable.get("db_password")

# Better - from Airflow Connection
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection("my_postgres")
```

## Best Practices

1. **Always use Git** - Even for "quick fixes"
2. **Test locally first** - Use Docker Compose on your machine
3. **Use branches** - Deploy from stable branch, not `main`
4. **Monitor logs** - Watch scheduler logs after deployment
5. **Version lock dependencies** - Pin versions in requirements
6. **Use environment variables** - Don't hardcode server-specific values
7. **Document changes** - Update CHANGELOG or commit messages

## Quick Reference

```bash
# Deploy from local machine
./deploy-to-remote.sh YOUR_IP

# Update on server (manual)
ssh root@YOUR_IP
cd ~/liquor_app && git pull
cd ~/airflow && docker compose restart airflow-scheduler

# Check DAG status
ssh root@YOUR_IP "docker compose -f ~/airflow/docker-compose.yaml run airflow-cli airflow dags list"

# View DAG errors
ssh root@YOUR_IP "docker compose -f ~/airflow/docker-compose.yaml run airflow-cli airflow dags list-import-errors"
```

## Recommended Workflow

For this project, I recommend:

**Development:**
1. Make changes locally
2. Test with local Airflow Docker setup
3. Commit to Git
4. Push to GitHub

**Deployment:**
1. SSH to server: `ssh root@YOUR_IP`
2. Update repo: `cd ~/liquor_app && git pull`
3. Restart scheduler: `cd ~/airflow && docker compose restart airflow-scheduler`
4. Verify in UI: http://YOUR_IP:8080

Or use the automated script:
```bash
./deploy-to-remote.sh YOUR_IP
```
