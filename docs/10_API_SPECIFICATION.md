# ShiVi: OpenAPI & REST Endpoint Specification

## 1. Authentication & Identity Endpoints

### `POST /v1/auth/login`
- **Roles:** Public
- **Request Body:**
  ```json
  { "username": "commander_sharma", "password": "shivi_password" }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "username": "commander_sharma",
    "role": "SUPERVISOR",
    "tenant_id": "11111111-1111-1111-1111-111111111111"
  }
  ```

---

## 2. Incident & Priority Endpoints

### `POST /v1/incidents`
- **Roles:** `CITIZEN`, `RESPONDER`, `SUPERVISOR`
- **Request Body:**
  ```json
  {
    "local_reference": "INC-LOCAL-01",
    "category": "RESCUE",
    "title": "3 Stranded Family Members",
    "description": "Rising floodwater near Sector 4 Bridge",
    "severity": "CRITICAL",
    "people_at_risk": 3,
    "latitude": 26.1856,
    "longitude": 91.7483,
    "location_name": "Sector 4 Bridge",
    "has_photo_evidence": true
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "id": "ed391777-9d86-474f-b2be-eb9270181fe2",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "priority_score": 76.5,
    "status": "REPORTED"
  }
  ```

---

## 3. Causal Synchronization Endpoints

### `POST /v1/sync/push`
- **Roles:** `RESPONDER`, `CITIZEN`, `SUPERVISOR`
- **Request Body:**
  ```json
  {
    "device_id": "sdrf-node-01",
    "events": [
      {
        "event_id": "EVT-01K-001",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "entity_type": "route_observation",
        "entity_id": "ROUTE-88",
        "event_type": "ROUTE_STATUS_UPDATED",
        "changes": { "status": { "base": "UNKNOWN", "new": "BLOCKED" } },
        "actor_id": "00000000-0000-0000-0000-000000000002",
        "device_id": "sdrf-node-01",
        "device_sequence": 12,
        "occurred_at": "2026-09-01T21:00:00Z",
        "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ]
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "processed_count": 1,
    "accepted_event_ids": ["EVT-01K-001"],
    "duplicate_event_ids": [],
    "conflicts_detected": 0,
    "server_cursor": "2026-09-01T21:00:05Z"
  }
  ```

---

## 4. Conflict Review & Adjudication Endpoints

### `POST /v1/conflicts/{id}/resolve`
- **Roles:** `SUPERVISOR`, `ADMIN`
- **Request Body:**
  ```json
  {
    "resolved_value": "BLOCKED",
    "reason": "Drone imagery confirms bridge railing failure under 4ft water. Declared impassable."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "id": "69d9ec2c-9352-493c-a095-185aa8471232",
    "status": "RESOLVED",
    "resolved_value": "BLOCKED",
    "resolution_reason": "Drone imagery confirms bridge railing failure under 4ft water. Declared impassable."
  }
  ```

---

## 5. Verification & Audit Endpoints

### `POST /v1/verifications`
- **Roles:** `SUPERVISOR`
- **Request Body:**
  ```json
  {
    "task_id": "4fc77cd8-cb93-4591-b737-b5443cb88df5",
    "is_approved": true,
    "notes": "Verified 3 civilians accommodated at Sector 4 Relief Camp."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "task_status": "VERIFIED",
    "incident_status": "RESOLVED"
  }
  ```
