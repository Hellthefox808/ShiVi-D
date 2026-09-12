/**
 * ShiVi Operations Core API - Typed Client Service
 * =================================================
 *
 * Briefing:
 *     Central client-side communication layer for the ShiVi Common Operational Picture (COP).
 *     Provides strongly-typed, resilient HTTP communication with the FastAPI backend service.
 *     Handles dynamic API base URL resolution, bearer authentication token injection from localStorage,
 *     timeout safety via AbortController (preventing UI hangs during network blackouts), granular error
 *     message extraction from FastAPI JSON validation envelopes, and tactical operations endpoints.
 *
 * Reason:
 *     Disaster coordination environments operate across degraded and intermittent communication channels
 *     (cellular 4G/5G, low-bandwidth SATCOM, and offline local mesh). The web dashboard requires a single,
 *     robust API service that encapsulates network timeout guards, standardized error unwrapping,
 *     and typed schemas matching the backend models (incidents, tasks, conflicts, mesh framing, and SMS).
 */

// Explanation: Dynamically resolves backend base URL from environment variables, defaulting to local FastAPI port 8000.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Briefing:
 *     Typed schema for disaster incidents displayed in the tactical COP feed and map markers.
 *
 * Reason:
 *     Matches the backend `Incident` model. Includes explainable priority breakdown components
 *     and safety freeze flags (such as `is_route_blocked`) to indicate dangerous access corridors.
 */
export interface IncidentItem {
  // Explanation: Unique UUID identifying the incident canonical record.
  id: string;
  // Explanation: Human-readable localized identifier (e.g., 'INC-GUW-2026-001') for radio brevity.
  local_reference: string;
  // Explanation: Concise tactical summary of the disaster event.
  title: string;
  // Explanation: Detailed situational report or caller transcript notes.
  description?: string;
  // Explanation: Operational taxonomy defining the required emergency response branch.
  category: "RESCUE" | "MEDICAL" | "FLOOD_HAZARD" | "SHELTER" | "SUPPLY";
  // Explanation: Life-safety severity level used as a primary weight in priority scoring.
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  // Explanation: Workflow state in the ShiVi incident lifecycle.
  status: "DRAFT" | "REPORTED" | "TRIAGED" | "ASSIGNED" | "IN_PROGRESS" | "AWAITING_VERIFICATION" | "RESOLVED" | "CLOSED";
  // Explanation: Headcount of human lives in immediate jeopardy.
  people_at_risk: number;
  // Explanation: Normalized multi-factor priority index in the range [0.0, 100.0].
  priority_score: number;
  // Explanation: Named landmark or geographic sector designation.
  location_name?: string;
  // Explanation: WGS-84 latitude coordinate.
  latitude: number;
  // Explanation: WGS-84 longitude coordinate.
  longitude: number;
  // Explanation: Explainable scoring breakdown for supervisory auditing.
  priority_breakdown?: {
    severity_component?: number;
    people_component?: number;
    urgency_component?: number;
    category_component?: number;
    confidence_component?: number;
    explanation?: string;
  };
  // Explanation: Safety freeze flag indicating if access routes are blocked or contradicted.
  is_route_blocked?: boolean;
}

/**
 * Briefing:
 *     Typed schema for causal conflict cases requiring supervisor adjudication.
 *
 * Reason:
 *     Encapsulates competing field observations (e.g. Route USABLE vs BLOCKED).
 *     Maintains the array of competing actor claims and lists frozen dependent entities.
 */
export interface ConflictCaseItem {
  // Explanation: Unique UUID for the conflict case.
  id: string;
  // Explanation: Type of domain entity experiencing the contradiction ('ROUTE_OBSERVATION', 'INCIDENT', etc.).
  entity_type: string;
  // Explanation: Target entity ID under causal safety freeze.
  entity_id: string;
  // Explanation: Specific property name that collided (e.g., 'status', 'passable').
  conflicting_field: string;
  // Explanation: Resolution status of the conflict.
  status: "OPEN" | "RESOLVED" | "SUPERSEDED";
  // Explanation: List of competing claims submitted by field teams over various bearers.
  claims: Array<{
    actor_id: string;
    device_id: string;
    value: string;
    notes?: string;
    occurred_at: string;
    evidence_ids?: string[];
  }>;
  // Explanation: List of dependent tasks or routes locked until conflict adjudication.
  frozen_dependencies: string[];
  // Explanation: Adjudicated canonical value selected by the human supervisor.
  resolved_value?: string;
  // Explanation: Operational justification recorded for legal compliance and audit.
  resolution_reason?: string;
}

/**
 * Briefing:
 *     Typed schema for tactical field assignments and rescue tasks.
 *
 * Reason:
 *     Represents actionable work units linked to parent incidents. Tasks enforce
 *     causal route coupling; if `is_route_blocked` is true, dispatch is locked.
 */
export interface TaskItem {
  // Explanation: Unique UUID of the task.
  id: string;
  // Explanation: Parent incident ID that generated this task.
  incident_id: string;
  // Explanation: Tactical title describing the assignment.
  title: string;
  // Explanation: Detailed operational instructions and equipment requirements.
  description?: string;
  // Explanation: Functional categorization (e.g., 'EVACUATION', 'AIRLIFT', 'SUPPLY_DROP').
  task_type: string;
  // Explanation: Lifecycle status ('PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED').
  status: string;
  // Explanation: ID of the assigned responder or field unit.
  assigned_to_user_id?: string;
  // Explanation: Associated transit route corridor ID.
  route_id?: string;
  // Explanation: Flag indicating if the transit route is currently frozen or impassable.
  is_route_blocked?: boolean;
}

/**
 * Briefing:
 *     Typed schema for immutable compliance audit entries.
 *
 * Reason:
 *     Provides tamper-evident event records displayed in the audit timeline,
 *     tracking who performed what action, when, and under what justification.
 */
export interface AuditRecordItem {
  // Explanation: Unique UUID for the audit record.
  id: string;
  // Explanation: High-level operational action name (e.g., 'SUPERVISOR_CONFLICT_ADJUDICATION').
  action: string;
  // Explanation: User ID of the initiating operator.
  actor_id: string;
  // Explanation: Role of the actor ('FIELD_RESPONDER', 'INCIDENT_COMMANDER', 'SYSTEM').
  actor_role: string;
  // Explanation: Target domain entity classification.
  target_entity_type: string;
  // Explanation: Target entity UUID.
  target_entity_id: string;
  // Explanation: Human rationale provided for critical overrides.
  reason?: string;
  // Explanation: ISO-8601 UTC timestamp of the audit event.
  timestamp: string;
}

/**
 * Briefing:
 *     Typed schema for high-level incident command dashboard telemetry.
 *
 * Reason:
 *     Aggregates global system state into single-glance metrics including saturation indices,
 *     active safety freezes, responder counts, and sync health.
 */
export interface DashboardSummaryData {
  // Explanation: Total count of all recorded incidents across all states.
  total_incidents: number;
  // Explanation: Count of incidents requiring active intervention.
  open_incidents: number;
  // Explanation: Count of incidents successfully mitigated and verified.
  resolved_incidents: number;
  // Explanation: Count of P0 incidents posing imminent threat to life.
  critical_incidents: number;
  // Explanation: Count of tactical tasks currently underway in the field.
  active_tasks: number;
  // Explanation: Count of unresolved data contradictions requiring supervisor action.
  open_conflicts: number;
  // Explanation: Number of field personnel currently transmitting heartbeats.
  active_responders: number;
  // Explanation: Number of emergency physical assets ready for deployment.
  available_assets: number;
  // Explanation: Percentage (0-100) of available resources committed to missions.
  resource_saturation_index: number;
  // Explanation: Number of active safety freezes halting automated execution.
  active_safety_freezes: number;
  // Explanation: Operational health classification ('HEALTHY', 'DEGRADED', 'OFFLINE').
  sync_health_status: string;
  // Explanation: Indicates whether this summary was served from memory cache (TTL 5s).
  cached: boolean;
  // Explanation: ISO-8601 generation timestamp.
  generated_at: string;
}

/**
 * Briefing:
 *     Discrete execution step within an automated P0 disaster simulation drill.
 */
export interface SimulationStep {
  // Explanation: 1-indexed sequential step identifier.
  step: number;
  // Explanation: Tactical title of the simulation event.
  title: string;
  // Explanation: Technical description of the invariant being verified.
  detail: string;
  // Explanation: Raw structured payload processed during this step.
  payload: Record<string, any>;
}

/**
 * Briefing:
 *     Response envelope returned upon completion of an end-to-end disaster drill.
 */
export interface SimulationResponse {
  // Explanation: Status of the simulation run ('SUCCESS', 'FAILED').
  status: string;
  // Explanation: Unique identifier generated for the simulation run.
  simulation_id: string;
  // Explanation: ISO-8601 UTC execution timestamp.
  executed_at: string;
  // Explanation: High-level narrative summary of simulation findings.
  summary: string;
  // Explanation: Chronological sequence of verified drill steps.
  steps: SimulationStep[];
  // Explanation: Canonical incident state produced by the drill.
  incident: {
    id: string;
    title: string;
    priority_score: number;
    status: string;
    people_at_risk: number;
  };
  // Explanation: Causal conflict case created and adjudicated during the drill.
  conflict: {
    id: string;
    entity_id: string;
    status: string;
    resolved_value?: string;
    reason?: string;
  };
  // Explanation: Task dispatched or frozen during the drill.
  task: {
    id: string;
    status: string;
    route_id?: string;
  };
  // Explanation: Cryptographic evidence generated to verify ground truth.
  evidence: {
    id: string;
    sha256_hash: string;
  };
}

/**
 * Briefing:
 *     Telemetry record for a single phase within the ShiVi 14-phase operational lifecycle.
 */
export interface ContextLoopPhase {
  // Explanation: Numerical sequence position (1 through 14).
  phase_number: number;
  // Explanation: Concise alphanumeric code (e.g., 'P01_CAP', 'P05_FRZ').
  code: string;
  // Explanation: Human-readable phase title.
  name: string;
  // Explanation: High-level operational group ('EDGE_CAPTURE', 'RECONCILIATION', etc.).
  stage: string;
  // Explanation: Operational health ('HEALTHY', 'DEGRADED', 'CONSTRAINED').
  status: string;
  // Explanation: Processing latency in milliseconds.
  latency_ms: number;
  // Explanation: Event processing throughput rate.
  throughput_events_sec: number;
  // Explanation: Architectural safety invariant guaranteed by this phase.
  invariant: string;
  // Explanation: Count of domain records actively managed in this phase.
  active_records: number;
  // Explanation: Extended operational metrics specific to the phase.
  details?: Record<string, any>;
}

/**
 * Briefing:
 *     Telemetry response representing the complete 14-phase ShiVi context loop.
 */
export interface ContextLoopResponse {
  // Explanation: Global lifecycle health status.
  loop_status: string;
  // Explanation: Total number of active phases (normally 14).
  total_phases: number;
  // Explanation: Boolean verification that feedback loops close deterministically.
  loop_closure_verified: boolean;
  // Explanation: Current operational cycle execution identifier.
  active_cycle_id: string;
  // Explanation: End-to-end telemetry feedback loop latency in milliseconds.
  feedback_latency_ms: number;
  // Explanation: Detailed array of phase telemetry records.
  phases: ContextLoopPhase[];
  // Explanation: ISO-8601 timestamp of telemetry capture.
  timestamp: string;
}

/**
 * Briefing:
 *     Typed schema for the Common Operational Picture (COP) tactical map layers.
 */
export interface TacticalMapData {
  // Explanation: Geographic incident operational zone and hydrological conditions.
  zone: {
    name: string;
    center: { lat: number; lng: number };
    flood_level_meters_above_danger: number;
    flow_velocity_mps: number;
    surge_trend: string;
    weather_condition: string;
  };
  // Explanation: Coordinates defining the flood inundation polygon contour.
  inundation_polygon: Array<{ lat: number; lng: number }>;
  // Explanation: Evacuation and access transit corridors with safety freeze status.
  corridors: Array<{
    id: string;
    name: string;
    status: "OPEN" | "BLOCKED" | "SAFETY_FREEZE";
    is_frozen: boolean;
    active_conflict_id?: string;
    hazard_description: string;
    waypoints: Array<{ lat: number; lng: number }>;
  }>;
  // Explanation: Critical physical infrastructure facilities (hospitals, shelters, ramps).
  infrastructure: Array<{
    id: string;
    name: string;
    type: "HOSPITAL" | "SHELTER" | "BOAT_RAMP" | "COMMAND_HUB";
    lat: number;
    lng: number;
    status: string;
    available_beds?: number;
    occupancy?: number;
    max_capacity?: number;
    active_boats?: number;
  }>;
  // Explanation: Field response teams, vehicles, and aerial reconnaissance drones.
  active_units: Array<{
    id: string;
    name: string;
    callsign: string;
    lat: number;
    lng: number;
    heading_degrees: number;
    battery_pct: number;
    connectivity: string;
    altitude_meters?: number;
    assigned_task: string;
  }>;
}

/**
 * Briefing:
 *     Typed schema for a single BLE 5.0 GATT / LoRa mesh fragmented transmission frame.
 */
export interface MeshFrame {
  // Explanation: Canonical packet UUID shared across all fragments.
  packet_id: string;
  // Explanation: 0-indexed fragment order sequence.
  chunk_index: number;
  // Explanation: Total number of fragments required to rebuild the packet.
  total_chunks: number;
  // Explanation: Base64-encoded binary chunk payload.
  chunk_payload_base64: string;
  // Explanation: ASCII text snippet for debugging and packet inspection.
  chunk_payload_text: string;
  // Explanation: Byte size of this fragment.
  chunk_bytes: number;
  // Explanation: 8-character hexadecimal CRC32 checksum of this frame.
  crc32: string;
  // Explanation: Number of mesh mesh hops traversed.
  hop_count: number;
}

/**
 * Briefing:
 *     Response envelope returned when splitting a large event payload into mesh MTU frames.
 */
export interface MeshPacketizeResponse {
  // Explanation: Unique packet UUID.
  packet_id: string;
  // Explanation: Byte size of the unfragmented source payload.
  total_original_bytes: number;
  // Explanation: Number of discrete frames generated.
  total_frames: number;
  // Explanation: Maximum transmission unit applied (e.g., 496 for BLE GATT).
  max_frame_bytes: number;
  // Explanation: Physical or radio bearer protocol used.
  bearer: string;
  // Explanation: Ordered array of generated mesh frames.
  frames: MeshFrame[];
}

/**
 * Briefing:
 *     Response envelope returned when reassembling mesh frames at the edge gateway.
 */
export interface MeshReassembleResponse {
  // Explanation: Unique packet UUID.
  packet_id: string;
  // Explanation: Status of reassembly ('COMPLETE', 'INCOMPLETE', 'CORRUPT').
  status: string;
  // Explanation: Number of frames successfully ingested.
  received_frames: number;
  // Explanation: Total frames expected.
  total_frames: number;
  // Explanation: Fully reconstructed UTF-8 JSON payload.
  reassembled_payload: string;
  // Explanation: SHA-256 cryptographic hash of the reassembled payload.
  integrity_hash_sha256: string;
  // Explanation: Verification that all frame-level CRC32 checksums passed.
  crc32_verified: boolean;
}

/**
 * Briefing:
 *     Response schema for multimodal voice triage and automated NLP entity extraction.
 */
export interface VoiceTriageResponse {
  // Explanation: BCP-47 language code detected by transcription (e.g., 'hi', 'en', 'as').
  detected_language: string;
  // Explanation: Raw speech-to-text transcript.
  transcript: string;
  // Explanation: Structured disaster entities extracted by advisory AI models.
  extraction: {
    category: string;
    suggested_title: string;
    severity: string;
    estimated_people: number;
    extracted_hazards: string[];
    confidence: number;
  };
  // Explanation: Computed urgency score (0-100).
  urgency_score: number;
  // Explanation: Scoring factor weights explaining the urgency score.
  urgency_breakdown: Record<string, any>;
  // Explanation: Recommended NDMA Standard Operating Procedure guidelines.
  recommended_sop: {
    sop_code: string;
    title: string;
    mandatory_checklist: string[];
    safety_warnings: string[];
    required_equipment: string[];
    issuing_body: string;
  };
  // Explanation: Voice processing latency in milliseconds.
  transcription_latency_ms: number;
  // Explanation: SHA-256 hash of the prompt and transcript for reproducibility audit.
  prompt_hash: string;
}

/**
 * Briefing:
 *     Metadata schema describing an operational disaster drill scenario.
 */
export interface SimulationScenario {
  // Explanation: Alphanumeric scenario slug (e.g., 'scenario-flood-contradiction').
  id: string;
  // Explanation: Human-readable scenario name.
  name: string;
  // Explanation: Operational disaster domain.
  category: string;
  // Explanation: Severity rating.
  severity: string;
  // Explanation: List of core ShiVi safety invariants tested by this drill.
  invariants_tested: string[];
  // Explanation: Narrative summary of the disaster drill narrative.
  description: string;
  // Explanation: Typical execution time in milliseconds.
  duration_ms: number;
}

/**
 * ShiVi API Client Service
 * ========================
 *
 * Briefing:
 *     Singleton service managing all typed REST communications with the ShiVi backend.
 *     Implements automatic Authorization header injection, request timeout cancellation,
 *     and standardized JSON error parsing.
 *
 * Reason:
 *     Consolidates network access into a single auditable class, insulating React components
 *     from low-level HTTP mechanics, URL formation, and exception handling.
 */
class ApiService {
  // Explanation: Base URL pointing to the FastAPI backend service.
  private baseUrl: string;

  /**
   * Briefing:
   *     Initializes the API client service with configured base URL.
   */
  constructor() {
    this.baseUrl = API_BASE;
  }

  /**
   * Briefing:
   *     Low-level request dispatcher with timeout guards and token injection.
   *
   * Reason:
   *     Disaster environments experience high packet loss and stalling. A 10-second
   *     AbortController timeout prevents UI thread exhaustion while fetching network resources.
   *
   * @param endpoint Target API path (e.g., '/v1/incidents').
   * @param options Standard Fetch RequestInit configuration.
   * @returns Deserialized JSON response typed to T.
   * @throws Error with parsed backend detail message or timeout notification.
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    // Explanation: Retrieve persistent JWT session token from browser local storage if available.
    const token = typeof window !== "undefined" ? localStorage.getItem("shivi_auth_token") : null;
    const authHeader: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...authHeader,
      ...((options.headers as Record<string, string>) || {}),
    };

    // Explanation: AbortController enforces a strict 10-second timeout on all outbound requests.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const res = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        let errorMsg = `API Error [${res.status}]`;
        try {
          const errData = await res.json();
          if (errData?.detail) {
            if (typeof errData.detail === "string") {
              errorMsg = errData.detail;
            } else if (Array.isArray(errData.detail)) {
              errorMsg = errData.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
            }
          }
        } catch {
          const rawText = await res.text().catch(() => "");
          if (rawText) errorMsg += `: ${rawText}`;
        }
        throw new Error(errorMsg);
      }
      return await res.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.warn(`[ApiService] Request to ${endpoint} failed:`, err.message);
      throw err;
    }
  }

  // =========================================================================
  // System Health & Telemetry Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Polls basic liveness health check endpoint.
   *
   * Reason:
   *     Used by the navbar status pill to render live connectivity vs cached offline mode.
   */
  async getHealth(): Promise<{ status: string; service: string; version: string }> {
    return this.request("/health");
  }

  /**
   * Briefing:
   *     Retrieves high-level dashboard KPIs and operational metrics.
   *
   * Reason:
   *     Feeds the primary incident command HUD counters (critical count, saturation index, freezes).
   */
  async getSummary(): Promise<DashboardSummaryData> {
    return this.request("/v1/dashboard/summary");
  }

  /**
   * Briefing:
   *     Retrieves GeoJSON spatial features for GIS rendering.
   */
  async getGeoJson(): Promise<any> {
    return this.request("/v1/dashboard/geojson");
  }

  // =========================================================================
  // Incident Management Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches list of active disaster incidents.
   */
  async getIncidents(): Promise<IncidentItem[]> {
    return this.request("/v1/incidents");
  }

  /**
   * Briefing:
   *     Submits a newly reported incident from the field or dispatch console.
   */
  async createIncident(data: Partial<IncidentItem>): Promise<IncidentItem> {
    return this.request("/v1/incidents", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // =========================================================================
  // Tactical Task Dispatch Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches operational tasks and assignments across all sectors.
   */
  async getTasks(): Promise<TaskItem[]> {
    return this.request("/v1/tasks");
  }

  /**
   * Briefing:
   *     Assigns a tactical task to a specific responder or unit.
   *
   * Reason:
   *     Triggers route-safety validation on the backend. If the associated transit corridor
   *     is under safety freeze, this call is rejected to protect personnel safety.
   */
  async assignTask(taskId: string, userId: string): Promise<TaskItem> {
    return this.request(`/v1/tasks/${taskId}/assign`, {
      method: "POST",
      body: JSON.stringify({ assigned_to_user_id: userId }),
    });
  }

  // =========================================================================
  // Conflict Adjudication Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches all open causal conflict cases requiring supervisor review.
   */
  async getConflicts(): Promise<ConflictCaseItem[]> {
    return this.request("/v1/conflicts");
  }

  /**
   * Briefing:
   *     Adjudicates a causal conflict case, recording human justification and releasing safety freezes.
   *
   * Reason:
   *     Fulfills the core ShiVi principle that safety-critical contradictions must be resolved
   *     by human incident commanders with immutable audit rationale.
   *
   * @param conflictId Conflict case UUID.
   * @param resolvedValue Supervisor's chosen canonical state.
   * @param reason Human operational rationale for the decision.
   */
  async resolveConflict(
    conflictId: string,
    resolvedValue: string,
    reason: string
  ): Promise<ConflictCaseItem> {
    return this.request(`/v1/conflicts/${conflictId}/resolve`, {
      method: "POST",
      body: JSON.stringify({
        resolved_value: resolvedValue,
        reason,
      }),
    });
  }

  /**
   * Briefing:
   *     Triggers an active operational dispute between field claims to test human adjudication.
   */
  async triggerConflictDispute(data: {
    entity_id?: string;
    route_name?: string;
    claim_a_value?: string;
    claim_a_notes?: string;
    claim_b_value?: string;
    claim_b_notes?: string;
  } = {}): Promise<ConflictCaseItem> {
    return this.request("/v1/conflicts/trigger-dispute", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // =========================================================================
  // Immutable Audit Ledger Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches the chronological compliance audit timeline.
   */
  async getAuditTimeline(): Promise<AuditRecordItem[]> {
    return this.request("/v1/audit/timeline");
  }

  // =========================================================================
  // Physical Emergency Assets Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches inventory of deployed and available emergency physical assets.
   */
  async getAssets(): Promise<any[]> {
    return this.request("/v1/assets");
  }

  /**
   * Briefing:
   *     Claims physical custody of an asset or triggers automatic contention resolution.
   */
  async claimAsset(
    assetCode: string,
    data: {
      incident_id: string;
      task_id: string;
      claim_type: string;
      proof_data: Record<string, any>;
      priority_score: number;
    }
  ): Promise<any> {
    return this.request(`/v1/assets/${assetCode}/claim`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // =========================================================================
  // Governed Advisory AI Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Retrieves NDMA Standard Operating Procedure recommendations for an incident.
   */
  async getAiSop(category: string, severity: string): Promise<any> {
    return this.request(`/v1/ai/sop?category=${encodeURIComponent(category)}&severity=${encodeURIComponent(severity)}`);
  }

  /**
   * Briefing:
   *     Extracts structured disaster entities from raw multilingual field text.
   */
  async extractIncidentEntities(rawText: string, language: string = "en"): Promise<any> {
    return this.request("/v1/ai/extract", {
      method: "POST",
      body: JSON.stringify({ raw_text: rawText, language }),
    });
  }

  // =========================================================================
  // P0 Disaster Workflow Simulation Suite Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Triggers an end-to-end P0 disaster drill simulation on the backend.
   *
   * Reason:
   *     Demonstrates and validates all 8 phases of the ShiVi lifecycle, from offline outbox
   *     capture through causal safety freeze, supervisor adjudication, and audit logging.
   */
  async simulateWorkflow(scenarioId: string = "scenario-flood-contradiction"): Promise<SimulationResponse> {
    return this.request(`/v1/demo/simulate-workflow?scenario_id=${encodeURIComponent(scenarioId)}`, {
      method: "POST",
    });
  }

  /**
   * Briefing:
   *     Resets backend demonstration database state to default initial conditions.
   */
  async resetDemo(): Promise<{ status: string; message: string }> {
    return this.request("/v1/demo/reset", {
      method: "POST",
    });
  }

  // =========================================================================
  // Disaster SMS Gateway & Satellite Burst Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Simulates receipt of an inbound 2G GSM SMS emergency report.
   */
  async processInboundSms(senderPhone: string, messageText: string, gatewayType: string = "GSM_GATEWAY"): Promise<any> {
    return this.request("/v1/integrations/sms/inbound", {
      method: "POST",
      body: JSON.stringify({
        sender_phone: senderPhone,
        message_text: messageText,
        gateway_type: gatewayType,
      }),
    });
  }

  /**
   * Briefing:
   *     Broadcasts a localized SMS sector emergency warning to citizen phones.
   */
  async broadcastSectorAlert(data: {
    sector_name: string;
    hazard_type: string;
    severity?: string;
    instruction: string;
    recipient_phones?: string[];
  }): Promise<any> {
    return this.request("/v1/integrations/sms/broadcast", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Briefing:
   *     Encodes an incident event into a 140-byte compact satellite burst payload.
   */
  async encodeSatelliteBurst(data: {
    event_id: string;
    category: string;
    severity: string;
    people_at_risk: number;
    latitude: number;
    longitude: number;
    short_desc?: string;
  }): Promise<any> {
    return this.request("/v1/integrations/sms/compact/encode", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Briefing:
   *     Decodes a 140-byte compact satellite burst string into structured incident fields.
   */
  async decodeSatelliteBurst(burstString: string): Promise<any> {
    return this.request("/v1/integrations/sms/compact/decode", {
      method: "POST",
      body: JSON.stringify({ burst_string: burstString }),
    });
  }

  /**
   * Briefing:
   *     Retrieves historical log of transmitted and received SMS and satellite messages.
   */
  async getSmsLogs(): Promise<any[]> {
    return this.request("/v1/integrations/sms/logs");
  }

  /**
   * Briefing:
   *     Retrieves active telemetry across all 14 phases of the ShiVi context loop.
   */
  async getContextLoopStatus(): Promise<ContextLoopResponse> {
    return this.request("/v1/dashboard/context-loop");
  }

  // =========================================================================
  // Tactical COP Map Layers Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches real-time spatial layers (inundation zones, corridors, facilities, units).
   */
  async getTacticalMapLayers(): Promise<TacticalMapData> {
    return this.request("/v1/dashboard/map-layers");
  }

  // =========================================================================
  // BLE 5.0 GATT Mesh Packet Framing Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fragments a JSON payload into MTU-sized mesh transmission frames with CRC32 checksums.
   */
  async packetizeMeshPayload(
    payload: any,
    maxMtu: number = 496,
    bearer: string = "BLE_5.0_GATT"
  ): Promise<MeshPacketizeResponse> {
    return this.request("/v1/sync/mesh/packetize", {
      method: "POST",
      body: JSON.stringify({
        payload,
        max_mtu_bytes: maxMtu,
        bearer,
      }),
    });
  }

  /**
   * Briefing:
   *     Reassembles fragmented mesh frames into the original payload and validates SHA-256 integrity.
   */
  async reassembleMeshFrames(frames: MeshFrame[]): Promise<MeshReassembleResponse> {
    return this.request("/v1/sync/mesh/reassemble", {
      method: "POST",
      body: JSON.stringify({ frames }),
    });
  }

  // =========================================================================
  // Multimodal Voice Triage Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Dispatches voice transcript to NLP models for emergency entity extraction and SOP recommendation.
   */
  async voiceTriage(transcript: string, languageHint: string = "hi"): Promise<VoiceTriageResponse> {
    return this.request("/v1/ai/voice-triage", {
      method: "POST",
      body: JSON.stringify({
        simulated_transcript: transcript,
        language_hint: languageHint,
      }),
    });
  }

  // =========================================================================
  // Disaster Drill Scenarios Catalog Endpoints
  // =========================================================================

  /**
   * Briefing:
   *     Fetches catalog of available disaster scenarios for live simulation drills.
   */
  async getSimulationScenarios(): Promise<SimulationScenario[]> {
    return this.request("/v1/demo/scenarios");
  }
}

// Explanation: Export singleton instance for unified application-wide access.
export const api = new ApiService();
export default api;
