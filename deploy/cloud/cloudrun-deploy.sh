#!/usr/bin/env bash
# ==============================================================================
# ShiVi Google Cloud Run Serverless Deployment Script
# ==============================================================================
set -eo pipefail

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
REGION=${GCP_REGION:-"asia-south1"} # Default: Mumbai for Indian disaster zones

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GCP_PROJECT_ID is not set and no active gcloud project found."
    echo "Usage: GCP_PROJECT_ID=your-project-id ./cloudrun-deploy.sh"
    exit 1
fi

echo "================================================================================"
echo "  ☁️ SHIVI GOOGLE CLOUD RUN SERVERLESS DEPLOYMENT"
echo "  Project: $PROJECT_ID | Region: $REGION"
echo "================================================================================"

# 1. Deploy Backend API
echo "[1/2] Building & Deploying Backend Core API to Cloud Run..."
gcloud builds submit ./backend \
  --tag gcr.io/$PROJECT_ID/shivi-backend:latest \
  --project $PROJECT_ID

gcloud run deploy shivi-backend \
  --image gcr.io/$PROJECT_ID/shivi-backend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --set-env-vars "ENVIRONMENT=production,DATABASE_URL=sqlite+aiosqlite:////tmp/shivi.db,CORS_ORIGINS=*" \
  --project $PROJECT_ID

BACKEND_URL=$(gcloud run services describe shivi-backend --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID)
echo "✅ Backend deployed at: $BACKEND_URL"

# 2. Deploy Frontend COP Web Hub
echo "[2/2] Building & Deploying Frontend Web COP to Cloud Run..."
gcloud builds submit ./frontend \
  --tag gcr.io/$PROJECT_ID/shivi-frontend:latest \
  --project $PROJECT_ID

gcloud run deploy shivi-frontend \
  --image gcr.io/$PROJECT_ID/shivi-frontend:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 3000 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "NODE_ENV=production,PORT=3000,NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --project $PROJECT_ID

FRONTEND_URL=$(gcloud run services describe shivi-frontend --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

echo "================================================================================"
echo "  🎉 DEPLOYMENT COMPLETE!"
echo "  • Web Command Portal:     $FRONTEND_URL"
echo "  • Disaster SMS Lab:       $FRONTEND_URL/sms"
echo "  • Core API Swagger:       $BACKEND_URL/docs"
echo "  • Health Probe:           $BACKEND_URL/health"
echo "================================================================================"
