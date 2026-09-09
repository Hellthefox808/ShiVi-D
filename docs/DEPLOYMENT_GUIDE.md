# ShiVi Operational Deployment & Infrastructure Runbook

This runbook specifies deployment procedures across all operational tiers of the **ShiVi** platform: from single-laptop zero-docker tactical disaster outposts to highly resilient multi-cloud Kubernetes clusters.

---

## 1. Deployment Topology Matrix

| Deployment Tier | Target Environment | Tech Stack | Storage & Persistence | Typical Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Tactical Edge Post** | Rugged field laptop / Raspberry Pi 5 | Bare-metal Python + Next.js Standalone | SQLite WAL + Local Flash | Staging area, field triage tent, zero power grid |
| **Tier 2: Unified Container Post** | Mobile Command Vehicle / Edge Server | Docker Compose + Nginx Reverse Proxy | Docker Volumes (SQLite or PostGIS) | District Disaster Emergency Operations Center (DEOC) |
| **Tier 3: Enterprise Cloud Hub** | Kubernetes (K3s / GKE / AKS / EKS) | Multi-replica Pods + Ingress + Redis | PostgreSQL 16 + PostGIS + MinIO S3 | State / National Emergency Operations Center (SEOC / NEOC) |
| **Tier 4: Serverless Cloud Run** | Google Cloud Run / Azure Container Apps | Scaled-to-min-1 Managed Containers | Cloud SQL + Cloud Storage | High-concurrency citizen alert dissemination & live dashboard |

---

## 2. Quickstart: Unified Docker Production Deployment

### Automated One-Command Deploy (Linux / macOS)

```bash
# Clone and navigate to repository root
git clone https://github.com/Hellthefox808/ShiVi-D.git
cd ShiVi-D

# Execute automated deployment orchestrator
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh
```

### Automated One-Command Deploy (Windows PowerShell)

```powershell
# Open PowerShell in repository root
.\scripts\deploy_production.ps1
```

### Manual Docker Compose Commands

```bash
# Build production images with parallel build cache
docker compose -f docker-compose.prod.yml build

# Start services in detached background mode
docker compose -f docker-compose.prod.yml up -d

# Verify container health status
docker compose -f docker-compose.prod.yml ps
```

### Exposed Endpoints via Nginx Reverse Proxy (Port 80)
- **Web Command Portal & COP:** `http://localhost/`
- **Emergency SMS & Satellite Gateway Console:** `http://localhost/sms`
- **FastAPI OpenAPI Interactive Swagger:** `http://localhost/docs`
- **Core Edge Micro-Health Probe:** `http://localhost/health`
- **Internal Nginx Liveness:** `http://localhost/nginx-health`

---

## 3. Bare-Metal Tactical Edge Deployment (Zero Docker)

For disaster zones with no container runtime, deploy directly on host Python 3.10+ and Node.js 18+:

```bash
chmod +x scripts/deploy_baremetal.sh
./scripts/deploy_baremetal.sh
```

### Manual Process Execution

```bash
# 1. Backend Core API
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=8000 HOST=0.0.0.0 uvicorn app.main:app --workers 4 &

# 2. Frontend Web COP
cd ../frontend
npm ci
npm run build
PORT=3000 node scripts/run-next.js start &
```

---

## 4. Kubernetes Deployment (`deploy/k8s/`)

Deploy to any CNCF-conformant Kubernetes cluster (K8s, MicroK8s, K3s):

```bash
# 1. Create dedicated namespace
kubectl apply -f deploy/k8s/namespace.yaml

# 2. Apply ConfigMaps and Secrets
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secrets.yaml

# 3. Deploy Backend and Storage
kubectl apply -f deploy/k8s/backend-deployment.yaml

# 4. Deploy Frontend Web Hub
kubectl apply -f deploy/k8s/frontend-deployment.yaml

# 5. Apply Services & Ingress Controller
kubectl apply -f deploy/k8s/services.yaml
kubectl apply -f deploy/k8s/ingress.yaml

# 6. Verify rollout status
kubectl rollout status deployment/shivi-backend -n shivi-ops
kubectl rollout status deployment/shivi-frontend -n shivi-ops
```

---

## 5. Linux Systemd Service Daemonization (`deploy/systemd/`)

For persistent edge command servers:

```bash
# 1. Copy service descriptors
sudo cp deploy/systemd/shivi-backend.service /etc/systemd/system/
sudo cp deploy/systemd/shivi-frontend.service /etc/systemd/system/

# 2. Reload systemd daemon
sudo systemctl daemon-reload

# 3. Enable auto-start on system boot
sudo systemctl enable shivi-backend
sudo systemctl enable shivi-frontend

# 4. Start services immediately
sudo systemctl start shivi-backend
sudo systemctl start shivi-frontend

# 5. Verify service logs
sudo journalctl -u shivi-backend -f
```

---

## 6. Post-Deployment Automated Verification

Validate complete end-to-end operational health using the automated diagnostic suite:

```bash
# Run against local or remote deployment
python scripts/healthcheck.py http://localhost:8000
```

Sample output:
```text
================================================================================
  🏥 SHIVI POST-DEPLOYMENT AUTOMATED DIAGNOSTIC VALIDATOR
================================================================================
  Target Server: http://localhost:8000

ENDPOINT                         STATUS     LATENCY      RESULT     DESCRIPTION
--------------------------------------------------------------------------------
/health                          200 OK       0.82 ms    PASS       Core Micro-Health Probe
/v1/dashboard/summary            200 OK      12.45 ms    PASS       Incident Operations Center (IOC) Summary
/v1/dashboard/geojson            200 OK      21.10 ms    PASS       Geospatial Polygon Map Layer
/v1/incidents                    200 OK       6.15 ms    PASS       Incident Catalog Feed
/v1/conflicts/status             200 OK       4.30 ms    PASS       Causal Conflict Engine Status
/v1/assets/contention-status     200 OK       3.95 ms    PASS       Physical Asset Contention State
/v1/integrations/sms/logs        200 OK       2.80 ms    PASS       Disaster SMS & Satellite Ledger
/v1/audit/ledger                 200 OK       5.20 ms    PASS       Cryptographic Audit Ledger Chain
/docs                            200 OK       3.10 ms    PASS       OpenAPI Swagger Interactive Documentation
--------------------------------------------------------------------------------
  Average Endpoint Latency: 6.65 ms

  ✅ ALL CRITICAL PIPELINE SERVICES VERIFIED OPERATIONAL & HEALTHY
```

---

## 7. Security Hardening & Backup Protocol

1. **Cryptographic Secret Rotation:**
   - Rotate `JWT_SECRET` prior to operational mobilization using `openssl rand -hex 32`.
2. **Database Snapshot Backups:**
   - Automated zero-downtime hot backups via SQLite VACUUM INTO:
     ```bash
     python backend/scripts/backup_and_clean_db.py
     ```
3. **Audit Ledger Verification:**
   - Verify cryptographic non-repudiation of hash chains:
     ```bash
     curl -s http://localhost:8000/v1/audit/ledger/verify | jq .
     ```

---

## 8. Vercel Cloud Deployment (Command Center Web Frontend)

The Next.js 14 Web Command Center can be deployed to **Vercel** with zero friction:

### Option A: Standard Root Directory Setting (Recommended)
1. In the Vercel Dashboard, click **Add New... $\to$ Project** and select `Hellthefox808/ShiVi-D`.
2. Under **Project Settings $\to$ Root Directory**, click **Edit** and set it to:
   ```text
   frontend
   ```
3. Framework Preset: **Next.js** (auto-detected).
4. Environment Variables:
   - Add `NEXT_PUBLIC_API_URL` pointing to your deployed backend URL (e.g. `https://your-backend.railway.app` or Google Cloud Run URL).
5. Click **Deploy**.

### Option B: Monorepo Root Deployment (Automatic via `vercel.json`)
If you leave the Root Directory as `./` (default):
- Vercel will automatically read the root [vercel.json](file:///d:/HACKTHON/ShiVi%20-d/vercel.json) and root `package.json` workspaces:
  - Install Command: `npm install --prefix frontend`
  - Build Command: `npm run build --prefix frontend`
  - Output Directory: `frontend/.next`
- Add `NEXT_PUBLIC_API_URL` under Environment Variables and click **Deploy**.

