# Production Deployment & Nginx Setup for portal.t4f-global.org

This guide details how to deploy **Tech4Future-Global Management System V13** to your VPS for **`portal.t4f-global.org`**, resolve port 8000 conflicts, and configure GitHub Actions CI/CD.

---

## 1. ⚠️ Port 8000 Conflict Resolution

Because **port 8000** is already in use by another application on your VPS:
- The container's application server binds to host port **`8080`** (or whichever port you specify in `.env` via `WEB_PORT=8080`).
- Container internal port 8000 is mapped via `8080:8000`, so port 8000 on the host is never touched.
- All Docker Compose files, Makefiles, and Nginx configurations are preconfigured to route to **`8080`**.

---

## 2. 🌐 Nginx Configuration for portal.t4f-global.org

Depending on your VPS setup, choose **Option A** (recommended if you already host other sites) or **Option B**:

### Option A: Host-Level Nginx (Shared VPS with other sites)
If your VPS already runs Nginx directly on the host (for example, hosting `jobportal.sbpafrica.group` on port 80/443):

1. **Copy the pre-configured Nginx site file to your VPS:**
   ```bash
   sudo cp docker/nginx/host-nginx-portal.t4f-global.org.conf /etc/nginx/sites-available/portal.t4f-global.org
   ```
2. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/portal.t4f-global.org /etc/nginx/sites-enabled/
   ```
3. **Verify syntax & reload Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```
4. **Provision Free SSL Certificate with Certbot:**
   ```bash
   sudo certbot --nginx -d portal.t4f-global.org
   ```

### Option B: Docker-Managed Nginx (Standalone Container)
If this project manages its own Nginx container directly through Docker Compose:
- The `nginx` container defined in `docker-compose.prod.yml` uses `docker/nginx/nginx.conf`.
- It listens on ports `80` and `443` and proxies internally to `web:8000`.
- To start:
  ```bash
  make prod-up
  ```

---

## 3. 🧪 Testing Environment Configuration (`.env`)

A ready-to-test `.env` file has been prepared in the repository root.

Key settings configured:
```ini
DJANGO_SECRET_KEY=5l39TFArzNCKOIn4sh93rC11WaC0iZRs3S-_bM02fQVpEEoZ_bkZx8t77RelZ0Q51-g
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=portal.t4f-global.org,localhost,127.0.0.1,web
DJANGO_CSRF_TRUSTED_ORIGINS=https://portal.t4f-global.org,http://portal.t4f-global.org,http://localhost:8080,http://127.0.0.1:8080
WEB_PORT=8080
HTTP_PORT=80
HTTPS_PORT=443
PORT=8080
DB_ENGINE=sqlite
```

To run the local testing server:
```bash
make dev
# Server starts on http://localhost:8080
```

To run with PostgreSQL and Redis via Docker Compose:
```bash
make docker-up
# Web platform available on http://localhost:8080
```

---

## 4. 🚀 GitHub Actions CI/CD Pipeline

The automated deployment pipeline is located at:
[`.github/workflows/deploy.yml`](file:///.github/workflows/deploy.yml)

### Workflow Steps:
1. **CI Quality Gate:** Runs on every push to `main` — installs Python 3.13 dependencies, executes `python backend/manage.py check`, and runs all integration/unit tests (`pytest backend/tests`).
2. **CD Deployment:** Once tests pass, automatically SSHs into your VPS, updates code from GitHub, builds Docker images, runs migrations, seeds users, collects static files, and verifies health.

### 🔐 GitHub Actions Secrets to Configure:
Navigate to your repository on GitHub: **Settings > Secrets and variables > Actions > New repository secret**:

| Secret Name | Description | Example / Value |
|---|---|---|
| `VPS_HOST` | VPS IP address or domain | `187.7.19.226` or your VPS IP |
| `VPS_USERNAME` | SSH user on your VPS | `root`, `erasmus`, or `sbpafrica` |
| `VPS_SSH_KEY` | Private SSH key with VPS access | Contents of your `~/.ssh/id_rsa` or private key |

### ⚙️ GitHub Actions Variables to Configure (Optional):
Under **Settings > Secrets and variables > Actions > Variables tab > New repository variable**:

| Variable Name | Description | Default if omitted |
|---|---|---|
| `VPS_PORT` | SSH port on VPS | `22` |
| `DEPLOY_PATH` | Full directory path on VPS | `/var/www/portal.t4f-global.org` |

---

## 5. 🛠️ Useful Makefile Commands

| Command | Action |
|---|---|
| `make dev` | Starts local development server on port **8080** |
| `make test` | Runs the Pytest suite |
| `make check` | Runs Django system checks |
| `make seed-users` | Seeds and verifies 15 accounts across all roles |
| `make prod-build` | Builds production Docker images |
| `make prod-up` | Starts production PostgreSQL, Redis, Web, and Nginx |
| `make prod-down` | Stops production containers |
| `make prod-migrate` | Runs database migrations in the production container |
| `make prod-seed` | Seeds user accounts in the production container |
| `make prod-logs` | Follows production container logs |
