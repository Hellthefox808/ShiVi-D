# ShiVi: Data Model and Event Contracts

## 1. Relational Entity Schema Definitions

### 1.1 Tenant & Identity
- **`tenants`**: `id` (PK, UUID), `name` (VARCHAR), `slug` (VARCHAR, UNIQUE), `sector_pack` (VARCHAR, DEFAULT 'disaster_response'), `created_at` (TIMESTAMPTZ).
- **`users`**: `id` (PK, UUID), `tenant_id` (FK), `username` (VARCHAR, UNIQUE), `email` (VARCHAR), `hashed_password` (VARCHAR), `full_name` (VARCHAR), `role` (VARCHAR: `CITIZEN`, `RESPONDER`, `SUPERVISOR`, `ADMIN`), `phone` (VARCHAR), `is_active` (BOOLEAN), `created_at` (TIMESTAMPTZ).
- **`devices`**: `id` (PK, UUID), `tenant_id` (FK), `user_id` (FK), `device_fingerprint` (VARCHAR), `last_sequence_number` (BIGINT), `is_revoked` (BOOLEAN), `registered_at` (TIMESTAMPTZ), `last_seen_at` (TIMESTAMPTZ).

### 1.2 Incidents & Route Observations
- **`incidents`**: `id` (PK, UUID), `tenant_id` (FK), `local_reference` (VARCHAR, INDEX), `category` (VARCHAR), `title` (VARCHAR), `description` (TEXT), `severity` (VARCHAR: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `status` (VARCHAR: `DRAFT`, `REPORTED`, `TRIAGED`, `ASSIGNED`, `IN_PROGRESS`, `AWAITING_VERIFICATION`, `RESOLVED`, `CLOSED`), `people_at_risk` (INT), `priority_score` (FLOAT), `priority_breakdown` (JSONB), `latitude` (FLOAT), `longitude` (FLOAT), `location_name` (VARCHAR), `created_by_user_id` (VARCHAR), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ), `version` (INT).
- **`route_observations`**: `id` (PK, UUID), `tenant_id` (FK), `route_identifier` (VARCHAR, INDEX), `status` (VARCHAR: `UNKNOWN`, `USABLE`, `BLOCKED`, `FLOODED`, `UNCERTAIN`), `notes` (JSONB Array), `photos` (JSONB Array), `last_reported_by` (VARCHAR), `last_reported_at` (TIMESTAMPTZ), `is_frozen` (VARCHAR: `TRUE`, `FALSE`), `active_conflict_id` (VARCHAR), `updated_at` (TIMESTAMPTZ).

### 1.3 Tasks, Conflict Cases & Evidence
- **`tasks`**: `id` (PK, UUID), `tenant_id` (FK), `incident_id` (FK), `title` (VARCHAR), `description` (TEXT), `task_type` (VARCHAR), `status` (VARCHAR: `CREATED`, `OFFERED`, `ACCEPTED`, `EN_ROUTE`, `ON_SITE`, `COMPLETED`, `VERIFIED`, `BLOCKED`, `CANCELLED`), `assigned_to_user_id` (VARCHAR), `assigned_team_id` (VARCHAR), `required_skills` (JSONB Array), `route_id` (VARCHAR), `is_route_blocked` (VARCHAR: `TRUE`, `FALSE`), `created_at` (TIMESTAMPTZ), `accepted_at` (TIMESTAMPTZ), `completed_at` (TIMESTAMPTZ), `verified_at` (TIMESTAMPTZ), `version` (INT).
- **`conflict_cases`**: `id` (PK, UUID), `tenant_id` (FK), `entity_type` (VARCHAR), `entity_id` (VARCHAR), `conflicting_field` (VARCHAR), `status` (VARCHAR: `OPEN`, `RESOLVED`, `REOPENED`), `claims` (JSONB Array of Claim Objects), `frozen_dependencies` (JSONB Array of Task IDs), `resolved_by_user_id` (VARCHAR), `resolved_value` (VARCHAR), `resolution_reason` (TEXT), `resolved_at` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
- **`evidence`**: `id` (PK, UUID), `tenant_id` (FK), `task_id` (VARCHAR), `incident_id` (VARCHAR), `file_type` (VARCHAR: `IMAGE`, `AUDIO`, `GPS_TRACK`), `file_path` (VARCHAR), `sha256_hash` (VARCHAR, 64-char hex), `byte_size` (INT), `latitude` (FLOAT), `longitude` (FLOAT), `gps_accuracy_meters` (FLOAT), `captured_by_user_id` (VARCHAR), `device_id` (VARCHAR), `captured_at` (TIMESTAMPTZ), `uploaded_at` (TIMESTAMPTZ), `is_verified` (VARCHAR: `TRUE`, `FALSE`), `verified_by_user_id` (VARCHAR), `verification_notes` (TEXT).

### 1.4 Operational Events & Audit Ledger
- **`operational_events`**: `id` (PK, UUID), `tenant_id` (FK), `event_id` (VARCHAR, UNIQUE, INDEX), `entity_type` (VARCHAR), `entity_id` (VARCHAR, INDEX), `event_type` (VARCHAR), `changes` (JSONB), `actor_id` (VARCHAR), `device_id` (VARCHAR), `device_sequence` (INT), `occurred_at` (TIMESTAMPTZ), `received_at` (TIMESTAMPTZ), `version_vector` (JSONB), `evidence_ids` (JSONB Array), `integrity_hash` (VARCHAR, 64-char hex).
- **`audit_entries`**: `id` (PK, UUID), `tenant_id` (FK), `action` (VARCHAR), `actor_id` (VARCHAR), `actor_role` (VARCHAR), `target_entity_type` (VARCHAR), `target_entity_id` (VARCHAR), `previous_state` (JSONB), `new_state` (JSONB), `reason` (TEXT), `timestamp` (TIMESTAMPTZ), `ip_address` (VARCHAR).

---

## 2. Canonical JSON Event Envelope

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ShiViOperationalEventEnvelope",
  "type": "object",
  "required": [
    "event_id",
    "tenant_id",
    "entity_type",
    "entity_id",
    "event_type",
    "changes",
    "actor_id",
    "device_id",
    "device_sequence",
    "occurred_at",
    "version_vector",
    "schema_version",
    "integrity_hash"
  ],
  "properties": {
    "event_id": { "type": "string" },
    "tenant_id": { "type": "string", "format": "uuid" },
    "entity_type": { "type": "string", "enum": ["incident", "task", "assignment", "resource", "route_observation", "conflict_case", "verification"] },
    "entity_id": { "type": "string" },
    "event_type": { "type": "string" },
    "changes": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["new"],
        "properties": {
          "base": {},
          "new": {}
        }
      }
    },
    "actor_id": { "type": "string", "format": "uuid" },
    "device_id": { "type": "string" },
    "device_sequence": { "type": "integer", "minimum": 1 },
    "occurred_at": { "type": "string", "format": "date-time" },
    "version_vector": { "type": "object", "additionalProperties": { "type": "integer" } },
    "evidence_ids": { "type": "array", "items": { "type": "string", "format": "uuid" } },
    "schema_version": { "type": "integer", "const": 1 },
    "integrity_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
  }
}
```
