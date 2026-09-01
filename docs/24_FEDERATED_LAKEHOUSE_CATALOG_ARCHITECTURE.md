# ShiVi: Cross-Cloud Federated Lakehouse Catalog Architecture & Pipeline

## 1. Executive Summary & Cross-Cloud Interoperability

In large-scale public safety, municipal infrastructure, and disaster management operations, historical data assets (e.g., historical flood maps, satellite telemetry, hydro-meteorological models, population censuses, and ERP financials) often reside in external cloud data lakes—such as **AWS S3 / AWS Glue Data Catalog** or **Databricks Unity Catalog**.

By leveraging **Google Cloud BigLake Iceberg Federated Catalogs**, ShiVi enables **zero-copy, cross-cloud analytical pipelines**:

- Query remote Apache Iceberg tables residing in AWS S3 or Databricks without expensive, slow, or brittle ETL data copying.
- Perform unified geospatial joins in BigQuery combining live ShiVi field incidents with historical satellite inundation layers stored in remote AWS/Databricks lakehouses.

```text
[AWS S3 / Databricks Unity]                 [Google Cloud Platform]
 (Remote Iceberg Tables)                    
           │                                          │
           │ (Read-Only REST Metadata Sync)           │
           ▼                                          ▼
 [AWS Glue / Unity Catalog] ──(OIDC Federation)──> [Google BigLake Iceberg Catalog]
                                                      (Catalog Type: 'federated')
                                                              │
                                                              ▼
                                                   [BigQuery / Spark Engine]
                                                (Unified Analytical SQL & GeoJoins)
```

---

## 2. End-to-End Federation Pipeline Setup

### 2.1 Pipeline Flow A: Databricks Unity Catalog Federation

#### Step 1: Regional Secret Management

Store the Databricks OAuth Service Principal in Secret Manager in the **same region** as the Lakehouse catalog (e.g., `asia-south1` for Mumbai / `us-east4` for US East):

```bash
# Set Secret Manager regional endpoint override
gcloud config set api_endpoint_overrides/secretmanager https://secretmanager.asia-south1.rep.googleapis.com/

# Create regional secret
gcloud secrets create databricks-shivi-secret \
  --location="asia-south1" \
  --project="shivi-enterprise" \
  --data-file=credentials.json
```

#### Step 2: Create Federated BigLake Iceberg Catalog

```bash
gcloud alpha biglake iceberg catalogs create unity_disaster_lakehouse \
   --project="shivi-enterprise" \
   --primary-location="asia-south1" \
   --catalog-type="federated" \
   --federated-catalog-type="unity" \
   --secret-name="projects/shivi-enterprise/locations/asia-south1/secrets/databricks-shivi-secret" \
   --unity-instance-name="https://dbc-xxxx.cloud.databricks.com" \
   --unity-catalog-name="disaster_management_catalog" \
   --refresh-interval="300s"
```

#### Step 3: Grant BigLake Service Agent Access

```bash
# Retrieve provisioned service account email
SERVICE_ACCOUNT=$(gcloud alpha biglake iceberg catalogs describe unity_disaster_lakehouse \
    --project="shivi-enterprise" \
    --location="asia-south1" \
    --format="value(biglake-service-account-id)")

# Grant secret accessor permission
gcloud secrets add-iam-policy-binding databricks-shivi-secret \
  --project="shivi-enterprise" \
  --location="asia-south1" \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

---

### 2.2 Pipeline Flow B: AWS Glue Data Catalog Federation

#### Step 1: AWS IAM Web Identity Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:aud": ["<GOOGLE_BIGLAKE_SERVICE_ACCOUNT_ID>"],
          "accounts.google.com:sub": ["<GOOGLE_BIGLAKE_SERVICE_ACCOUNT_ID>"]
        }
      }
    }
  ]
}
```

#### Step 2: Scoped AWS Glue & S3 Permissions Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GlueCatalogRead",
      "Effect": "Allow",
      "Action": [
        "glue:GetCatalog",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables"
      ],
      "Resource": "arn:aws:glue:ap-south-1:123456789012:catalog"
    },
    {
      "Sid": "S3LakehouseRead",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::disaster-telemetry-lakehouse",
        "arn:aws:s3:::disaster-telemetry-lakehouse/*"
      ]
    }
  ]
}
```

#### Step 3: Create BigLake Glue Federated Catalog

```bash
gcloud alpha biglake iceberg catalogs create glue_telemetry_lakehouse \
  --project="shivi-enterprise" \
  --primary-location="asia-south1" \
  --catalog-type="federated" \
  --federated-catalog-type="glue" \
  --glue-warehouse="123456789012" \
  --glue-aws-region="ap-south-1" \
  --glue-aws-role-arn="arn:aws:iam::123456789012:role/ShiviBigLakeFederationRole"
```

---

## 3. Optimal Region Pairing Matrix

To minimize cross-cloud latency and network egress costs:

| AWS Remote Region | Optimal GCP BigLake Region | Connectivity Tier |
| :--- | :--- | :--- |
| **AWS `ap-south-1` (Mumbai)** | **GCP `asia-south1` (Mumbai)** | **Low Latency Dedicated** |
| **AWS `us-east-1` (N. Virginia)** | **GCP `us-east4` (Ashburn, VA)** | **Low Latency Dedicated** |
| **AWS `us-west-2` (Oregon)** | **GCP `us-west1` (The Dalles, OR)** | **Low Latency Dedicated** |
| **AWS `eu-west-2` (London)** | **GCP `europe-west2` (London)** | **Low Latency Dedicated** |
| **AWS `eu-central-1` (Frankfurt)** | **GCP `europe-west3` (Frankfurt)** | **Low Latency Dedicated** |

---

## 4. Analytical BigQuery SQL Pipeline Examples

### 4.1 Cross-Cloud Risk & Response Spatial Query

```sql
-- Query live ShiVi incidents joined with historical AWS Glue Iceberg flood risk models
SELECT 
    inc.id AS incident_id,
    inc.title,
    inc.priority_score,
    inc.people_at_risk,
    flood_model.inundation_depth_meters,
    flood_model.critical_infrastructure_risk
FROM `shivi-enterprise.public_safety.incidents` AS inc
JOIN `shivi-enterprise.glue_telemetry_lakehouse.historical_gis.brahmaputra_flood_models` AS flood_model
  ON ST_DWithin(
      ST_GeogPoint(inc.longitude, inc.latitude),
      flood_model.geometry,
      250.0  -- 250 meter spatial buffer
  )
WHERE inc.status IN ('REPORTED', 'TRIAGED', 'ASSIGNED')
ORDER BY inc.priority_score DESC;
```
