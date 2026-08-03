# Mini Self-Hosted CI/CD Platform

A lightweight, self-hosted continuous integration and deployment platform for Node.js applications with zero-downtime blue-green deployments.

## Overview

Mini CI/CD eliminates the need for external CI/CD services while giving you complete control and visibility over every stage of your deployment pipeline. It receives GitHub webhooks, automatically clones your repository, installs dependencies, runs health checks, and switches traffic to the new deployment without downtime.

### Core Philosophy

- **Self-hosted**: Your code, your infrastructure, your rules
- **Zero-downtime**: Seamless deployments with automatic traffic switching via blue-green strategy
- **Transparent**: Understand every stage of the deployment pipeline through file-based logs
- **Automatic**: Deploy on every push with intelligent health checks and rollback support

## Architecture

```
Git Push -> GitHub Webhook -> HMAC Verification -> Build Queue
    -> Clone Repository -> npm ci -> Build & Deploy
    -> Start New Instance -> Health Check -> Switch Traffic -> Cleanup
```

### Components

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| **Webhook Server** | FastAPI | Receive and validate GitHub webhooks |
| **Build Queue** | File-based JSON | Manage pending and in-progress builds |
| **Build Worker** | Python threading | Execute build pipeline steps sequentially |
| **Deployer** | Python subprocess | Manage blue/green application instances |
| **Reverse Proxy** | FastAPI + httpx | Route traffic between active deployments |
| **Health Checker** | Python requests | Validate deployment health before switching |

### Deployment Strategy

The platform uses a **blue-green deployment** strategy:

- **Blue Environment**: Ports 3001, 3002
- **Green Environment**: Ports 3003, 3004

Only one environment is active at a time. On a new deployment, the platform starts the application on the inactive environment, runs health checks, and switches the reverse proxy to point to the new environment. If health checks fail, the deployment is aborted and traffic remains on the current environment.

## Features

- GitHub webhook receiver with HMAC signature verification
- File-based build queue with pending/in-progress/completed/failed states
- Automatic repository cloning and dependency installation via `npm ci`
- Blue-green zero-downtime deployments
- Round-robin load balancing across active deployment ports
- Automated health checks before traffic switching
- Manual rollback support to the previous deployment
- JSON-based deployment state persistence
- Log aggregation for build and deployment operations

## Project Structure

```
.
├── builder/
│   ├── main.py                 # FastAPI webhook receiver
│   ├── worker.py               # Background build worker
│   ├── buildQueue.py           # File-based queue management
│   ├── build_typing.py         # Type definitions
│   ├── deployer.py             # Blue-green deployment logic
│   ├── deployment_state.py     # State persistence
│   ├── health.py               # Health check utilities
│   ├── main.py                 # Webhook server entrypoint
│   ├── queue.json              # Queue storage
│   ├── deployment_state.json   # Deployment state storage
│   ├── pyproject.toml          # Python dependencies
│   └── uv.lock
├── loadbalancer/
│   ├── main.py                 # Reverse proxy and load balancer
│   ├── pyproject.toml
│   └── uv.lock
├── PRD.md
└── README.md
```

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for Python package management
- Node.js and npm (for building and running deployed applications)
- Git
- A GitHub repository with webhook access
- ngrok (or similar tunneling service) for exposing the webhook endpoint to GitHub

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ci-cdPipeline
```

### 2. Set Up the Builder

```bash
cd builder
uv sync
```

Create a `.env` file in the `builder` directory:

```env
GIT_WEBHOOK_SECRET=your_github_webhook_secret
REPO_URL=https://github.com/yourusername/your-repo.git
```

Create the initial state and version files:

```bash
echo '{"active": null, "blue": null, "green": null}' > deployment_state.json
echo '1' > .version
```

### 3. Set Up the Load Balancer

```bash
cd ../loadbalancer
uv sync
```

### 4. Prepare the Deployments Directory

```bash
mkdir -p ../deployments
```

## Usage

### 1. Start the Webhook Receiver

```bash
cd builder
uv run fastapi dev main.py --port 8000
```

The webhook server will start on `http://localhost:8000`.

### 2. Start the Load Balancer

In a separate terminal:

```bash
cd loadbalancer
uv run fastapi dev main.py --port 8080
```

The load balancer will start on `http://localhost:8080` and route traffic to the active deployment.

### 3. Expose the Webhook Endpoint

Use ngrok to expose your local webhook server to the internet:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`).

### 4. Configure the GitHub Webhook

1. Go to your GitHub repository
2. Navigate to **Settings > Webhooks > Add webhook**
3. Set **Payload URL** to your ngrok URL (e.g., `https://abc123.ngrok.io/`)
4. Set **Content type** to `application/json`
5. Set **Secret** to the same value as your `GIT_WEBHOOK_SECRET`
6. Select **Just the push event**
7. Click **Add webhook**

### 5. Trigger a Deployment

Push a commit to your repository:

```bash
git commit -m "Trigger deployment"
git push origin main
```

The webhook will trigger the build queue, and the worker will:

1. Clone the repository into `deployments/<commit-id>/`
2. Run `npm ci` to install dependencies
3. Start the application on the inactive environment (Blue or Green)
4. Run health checks on `http://127.0.0.1:<port>/health`
5. Switch traffic if health checks pass
6. Mark the build as completed

### 6. Access Your Application

Once deployed, access your application through the load balancer:

```bash
curl http://localhost:8080/
```

### API Endpoints

#### Builder (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Receive GitHub webhooks |
| `/health` | GET | Builder health check |
| `/queue` | GET | View current build queue |

#### Load Balancer (Port 8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{path}` | ANY | Proxy requests to active deployment |

### Monitoring

- **Build logs**: Check `builder/buildQueue.log` and `builder/gitWebhook.log`
- **Queue status**: `curl http://localhost:8000/queue`
- **Deployment state**: Inspect `builder/deployment_state.json`

### Rollback

If a deployment causes issues, you can trigger a rollback by calling the rollback function in `deployer.py`. The platform will switch traffic back to the previous environment if it passes health checks.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GIT_WEBHOOK_SECRET` | Yes | Secret key for validating GitHub webhook signatures |
| `REPO_URL` | Yes | Git repository URL to clone and deploy |
| `PORT` | No | Port for the deployed Node.js application (set automatically) |

## Deployed Application Requirements

The application being deployed must:

- Be a Node.js application with an entry point (e.g., `index.js`)
- Listen on the port provided via the `PORT` environment variable
- Expose a `GET /health` endpoint that returns HTTP 200 when healthy

Example minimal application:

```javascript
const express = require("express");
const app = express();

app.get("/", (req, res) => {
    res.json({ message: "Hello from deployment" });
});

app.get("/health", (req, res) => {
    res.status(200).json({ status: "healthy" });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure your code follows the existing style and includes appropriate logging for build and deployment operations.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Built for developers who want control over their deployment pipeline.
