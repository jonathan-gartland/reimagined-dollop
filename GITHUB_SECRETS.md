# GitHub Secrets Configuration

This document explains how to configure GitHub secrets for production deployment of the Airflow DAG.

## Why Use GitHub Secrets?

The `.env` file contains sensitive information (personal details, paths) that should not be committed to the repository. When deploying to production (e.g., hosted Airflow, Docker), these values should be stored as GitHub secrets and injected as environment variables.

## Required Secrets

Set these in your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**

### Database Configuration
```
DB_NAME=liquor_db
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### Git Configuration
```
GIT_AUTHOR_NAME=Your Name
GIT_AUTHOR_EMAIL=your.email@example.com
GIT_COMMITTER_NAME=Your Name
GIT_COMMITTER_EMAIL=your.email@example.com
```

### Project Paths
```
LIQUOR_APP_PATH=/path/to/liquor_app
CATALOG_BETA_PATH=/path/to/catalog-beta
```

### Airflow Configuration
```
AIRFLOW_DAG_OWNER=your_username
```

## Usage in GitHub Actions (Example)

If you deploy via GitHub Actions, you can inject these secrets:

```yaml
# .github/workflows/deploy-airflow.yml
name: Deploy Airflow DAG

on:
  push:
    branches: [main]
    paths:
      - 'dags/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Airflow
        env:
          DB_NAME: ${{ secrets.DB_NAME }}
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          GIT_AUTHOR_NAME: ${{ secrets.GIT_AUTHOR_NAME }}
          GIT_AUTHOR_EMAIL: ${{ secrets.GIT_AUTHOR_EMAIL }}
          GIT_COMMITTER_NAME: ${{ secrets.GIT_COMMITTER_NAME }}
          GIT_COMMITTER_EMAIL: ${{ secrets.GIT_COMMITTER_EMAIL }}
          LIQUOR_APP_PATH: ${{ secrets.LIQUOR_APP_PATH }}
          CATALOG_BETA_PATH: ${{ secrets.CATALOG_BETA_PATH }}
          AIRFLOW_DAG_OWNER: ${{ secrets.AIRFLOW_DAG_OWNER }}
        run: |
          # Your deployment commands here
          echo "Deploying with environment variables from secrets"
```

## Docker Compose Example

```yaml
# docker-compose.yml
services:
  airflow:
    image: apache/airflow:3.0.6
    environment:
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - GIT_AUTHOR_NAME=${GIT_AUTHOR_NAME}
      - GIT_AUTHOR_EMAIL=${GIT_AUTHOR_EMAIL}
      - GIT_COMMITTER_NAME=${GIT_COMMITTER_NAME}
      - GIT_COMMITTER_EMAIL=${GIT_COMMITTER_EMAIL}
      - LIQUOR_APP_PATH=${LIQUOR_APP_PATH}
      - CATALOG_BETA_PATH=${CATALOG_BETA_PATH}
      - AIRFLOW_DAG_OWNER=${AIRFLOW_DAG_OWNER}
    volumes:
      - ./dags:/opt/airflow/dags
```

Then create `.env` locally (gitignored) for development, and set as GitHub secrets for production.

## Local Development

For local development, keep using the `.env` file:

1. Copy `.env.example` to `.env`
2. Fill in your actual values
3. The DAG will automatically load from `.env`
4. Never commit `.env` (it's in `.gitignore`)

## Hosted Airflow Services

### Astronomer
Set environment variables in `airflow_settings.yaml`:
```yaml
env_vars:
  - name: DB_NAME
    value: liquor_db
  - name: GIT_AUTHOR_NAME
    value: Your Name
  # etc...
```

### AWS MWAA
Set in CloudFormation/Terraform:
```hcl
environment_variables = {
  DB_NAME = var.db_name
  GIT_AUTHOR_NAME = var.git_author_name
}
```

### Google Cloud Composer
Set via gcloud:
```bash
gcloud composer environments update ENVIRONMENT_NAME \
  --update-env-variables=DB_NAME=liquor_db,GIT_AUTHOR_NAME="Your Name"
```

## Security Best Practices

✅ **DO:**
- Use GitHub secrets for production
- Use `.env` for local development
- Add `.env` to `.gitignore`
- Rotate secrets periodically
- Use different values for dev/prod

❌ **DON'T:**
- Commit `.env` to version control
- Share secrets in Slack/email
- Use production secrets in development
- Store secrets in code comments
- Push secrets to public repositories

## Testing Secrets Locally

To test that your DAG works without hardcoded values:

```bash
# Clear environment
unset GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL

# Test DAG loads (should use defaults)
cd ~/airflow && source venv/bin/activate
python -c "from airflow.models import DagBag; DagBag(dag_folder='dags')"

# Set from .env and test
cd /Users/jonny/Projects/liquor_app
export $(cat .env | xargs)
cd ~/airflow && ./run-dag.sh
```

## Troubleshooting

**DAG uses wrong values:**
- Check `.env` file exists and has correct values
- Verify `load_dotenv()` path in DAG
- Check fallback defaults in `os.getenv()` calls

**Secrets not available in GitHub Actions:**
- Verify secrets are set in repository settings
- Check secret names match exactly (case-sensitive)
- Ensure workflow has correct `env:` mapping

**Docker container can't read .env:**
- Don't volume-mount `.env` (security risk)
- Pass as environment variables in docker-compose.yml
- Or use Docker secrets for swarm mode
