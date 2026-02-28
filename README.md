# n8n Multi-Worker Docker Setup

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

A Docker Compose configuration for running [n8n](https://n8n.io) in multi-worker mode with PostgreSQL, Redis, and a custom Python script runner.

**[한국어 문서 (Korean)](docs/ko/README.md)**

## Architecture

```
┌─────────────┐
│  n8n-main   │ ← Web UI & Workflow Management
│  (port:5678)│
└──────┬──────┘
       │
       ├─────→ PostgreSQL (Data Storage)
       │
       ├─────→ Redis (Job Queue)
       │            ↑
       │            │
       ├────────────┴─────────────┐
       │                          │
┌──────┴──────┐          ┌───────┴─────┐
│ n8n-worker-1│          │ n8n-worker-2│
│  (worker)   │          │  (worker)   │
└─────────────┘          └─────────────┘
       │                          │
       └──────────┬───────────────┘
                  │
          ┌───────┴───────┐
          │ python-runner │ ← Custom Python Script Execution
          │  (port:8000)  │
          └───────────────┘
```

## Components

| Service | Image | Role |
|---------|-------|------|
| **postgres** | postgres:15-alpine | Persistent data storage for workflows, users, and execution history |
| **redis** | redis:7-alpine | Bull Queue-based job queue for distributing workflow executions |
| **n8n-main** | n8nio/n8n:latest | Web UI, workflow editor, webhook receiver |
| **n8n-worker** | n8nio/n8n:latest | Dequeues and executes workflows from Redis. Horizontally scalable |
| **python-runner** | Custom (FastAPI) | HTTP server for executing Python scripts from n8n workflows |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/n8n_01.git
cd n8n_01
```

### 2. Configure environment

```bash
cp .env.example .env

# Generate secure passwords
openssl rand -base64 32  # Use for POSTGRES_PASSWORD
openssl rand -base64 32  # Use for N8N_ENCRYPTION_KEY
```

Edit `.env` and replace the placeholder values.

### 3. Start services

```bash
docker-compose up -d
```

Access n8n at **http://localhost:5678**. You will be prompted to create an admin account on first access.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | PostgreSQL password | (must change) |
| `N8N_ENCRYPTION_KEY` | Data encryption key | (must change) |
| `N8N_PORT` | n8n web port | 5678 |
| `N8N_WORKER_REPLICAS` | Number of worker instances | 2 |
| `N8N_WORKER_CONCURRENCY` | Concurrent workflows per worker | 10 |
| `GENERIC_TIMEZONE` | Timezone | Asia/Seoul |
| `N8N_LOG_LEVEL` | Log level (info, debug, error) | info |

## Scaling Workers

Adjust the number of workers in `.env`:

```bash
N8N_WORKER_REPLICAS=5
```

Then restart:

```bash
docker-compose up -d --scale n8n-worker=${N8N_WORKER_REPLICAS}
```

## Python Runner

The Python Runner is a FastAPI-based HTTP service that allows n8n workflows to execute Python scripts.

### Adding a script

1. Place your Python script in `python-runner/scripts/`
2. Add any dependencies to `python-runner/scripts/requirements.txt`
3. The runner auto-detects new dependencies and installs them

### Example usage

See `python-runner/scripts/hello.py` for a working example.

From n8n, use an HTTP Request node to call:
```
POST http://python-runner:8000/run
{
  "script": "hello.py",
  "args": ["--name", "World"]
}
```

## Operations

```bash
# View logs
docker-compose logs -f
docker-compose logs -f n8n-main
docker-compose logs -f n8n-worker

# Check status
docker-compose ps

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Backup

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U n8n_user n8n > backup_$(date +%Y%m%d).sql

# Export all workflows
docker-compose exec n8n-main n8n export:workflow --all --output=/home/node/.n8n/backup/
```

## Custom Nodes

Place custom n8n nodes in the `custom-nodes/` directory. They will be automatically loaded by n8n.

## Troubleshooting

### Workers not processing jobs
1. Check Redis: `docker-compose logs redis`
2. Check worker logs: `docker-compose logs n8n-worker`

### Database connection errors
```bash
docker-compose logs postgres
```

### Encryption key errors
All services (main and workers) must use the same `N8N_ENCRYPTION_KEY`.

## Security

1. Change all passwords in `.env` before first run
2. Set `N8N_ENCRYPTION_KEY` to a strong random string
3. Use HTTPS in production
4. Never commit `.env` to version control
5. Regularly backup your data

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

> **Note**: This project provides a Docker Compose deployment configuration. n8n itself is licensed under the [Sustainable Use License](https://github.com/n8n-io/n8n/blob/master/LICENSE.md).
