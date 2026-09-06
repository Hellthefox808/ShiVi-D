/**
 * ShiVi Operations Core API - Typed Client Service
 * Provides resilient, asynchronous communication with the FastAPI backend,
 * supporting dynamic base URL, timeout safety, and graceful local fallbacks.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface IncidentItem {
  id: string;
  local_reference: string;
  title: string;
  description?: string;
  category: "RESCUE" | "MEDICAL" | "FLOOD_HAZARD" | "SHELTER" | "SUPPLY";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "DRAFT" | "REPORTED" | "TRIAGED" | "ASSIGNED" | "IN_PROGRESS" | "AWAITING_VERIFICATION" | "RESOLVED" | "CLOSED";
  people_at_risk: number;
  priority_score: number;
  location_name?: string;
  latitude: number;
  longitude: number;
  priority_breakdown?: {
    severity_component?: number;
    people_component?: number;
    urgency_component?: number;
    category_component?: number;
    confidence_component?: number;
    explanation?: string;
  };
  is_route_blocked?: boolean;
}

export interface ConflictCaseItem {
  id: string;
  entity_type: string;
  entity_id: string;
  conflicting_field: string;
  status: "OPEN" | "RESOLVED" | "SUPERSEDED";
  claims: Array<{
    actor_id: string;
    device_id: string;
    value: string;
    notes?: string;
    occurred_at: string;
    evidence_ids?: string[];
  }>;
  frozen_dependencies: string[];
  resolved_value?: string;
  resolution_reason?: string;
}

export interface TaskItem {
  id: string;
  incident_id: string;
  title: string;
  description?: string;
  task_type: string;
  status: string;
  assigned_to_user_id?: string;
  route_id?: string;
  is_route_blocked?: boolean;
}

export interface AuditRecordItem {
  id: string;
  action: string;
  actor_id: string;
  actor_role: string;
  target_entity_type: string;
  target_entity_id: string;
  reason?: string;
  timestamp: string;
}

export interface DashboardSummaryData {
  total_incidents: number;
  open_incidents: number;
  resolved_incidents: number;
  critical_incidents: number;
  active_tasks: number;
  open_conflicts: number;
  active_responders: number;
  available_assets: number;
  resource_saturation_index: number;
  active_safety_freezes: number;
  sync_health_status: string;
  cached: boolean;
  generated_at: string;
}

export interface SimulationStep {
  step: number;
  title: string;
  detail: string;
  payload: Record<string, any>;
}

export interface SimulationResponse {
  status: string;
  simulation_id: string;
  executed_at: string;
  summary: string;
  steps: SimulationStep[];
  incident: {
    id: string;
    title: string;
    priority_score: number;
    status: string;
    people_at_risk: number;
  };
  conflict: {
    id: string;
    entity_id: string;
    status: string;
    resolved_value?: string;
    reason?: string;
  };
  task: {
    id: string;
    status: string;
    route_id?: string;
  };
  evidence: {
    id: string;
    sha256_hash: string;
  };
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

    try {
      const res = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errorBody = await res.text();
        throw new Error(`API Error [${res.status}]: ${errorBody}`);
      }
      return await res.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.warn(`[ApiService] Request to ${endpoint} failed:`, err.message);
      throw err;
    }
  }

  // Health check
  async getHealth(): Promise<{ status: string; service: string; version: string }> {
    return this.request("/health");
  }

  // Dashboard & Metrics
  async getSummary(): Promise<DashboardSummaryData> {
    return this.request("/v1/dashboard/summary");
  }

  async getGeoJson(): Promise<any> {
    return this.request("/v1/dashboard/geojson");
  }

  // Incidents
  async getIncidents(): Promise<IncidentItem[]> {
    return this.request("/v1/incidents");
  }

  async createIncident(data: Partial<IncidentItem>): Promise<IncidentItem> {
    return this.request("/v1/incidents", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Tasks
  async getTasks(): Promise<TaskItem[]> {
    return this.request("/v1/tasks");
  }

  async assignTask(taskId: string, userId: string): Promise<TaskItem> {
    return this.request(`/v1/tasks/${taskId}/assign`, {
      method: "POST",
      body: JSON.stringify({ assigned_to_user_id: userId }),
    });
  }

  // Conflicts & Adjudication
  async getConflicts(): Promise<ConflictCaseItem[]> {
    return this.request("/v1/conflicts");
  }

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

  // Audit Ledger
  async getAuditTimeline(): Promise<AuditRecordItem[]> {
    return this.request("/v1/audit/timeline");
  }

  // Assets
  async getAssets(): Promise<any[]> {
    return this.request("/v1/assets");
  }

  // AI Advisory
  async getAiSop(category: string, severity: string): Promise<any> {
    return this.request(`/v1/ai/sop?category=${encodeURIComponent(category)}&severity=${encodeURIComponent(severity)}`);
  }

  async extractIncidentEntities(rawText: string, language: string = "en"): Promise<any> {
    return this.request("/v1/ai/extract", {
      method: "POST",
      body: JSON.stringify({ raw_text: rawText, language }),
    });
  }

  // P0 Disaster Workflow Simulation
  async simulateWorkflow(): Promise<SimulationResponse> {
    return this.request("/v1/demo/simulate-workflow", {
      method: "POST",
    });
  }

  async resetDemo(): Promise<{ status: string; message: string }> {
    return this.request("/v1/demo/reset", {
      method: "POST",
    });
  }

  // Disaster SMS Gateway & Satellite Burst API
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

  async decodeSatelliteBurst(burstString: string): Promise<any> {
    return this.request("/v1/integrations/sms/compact/decode", {
      method: "POST",
      body: JSON.stringify({ burst_string: burstString }),
    });
  }

  async getSmsLogs(): Promise<any[]> {
    return this.request("/v1/integrations/sms/logs");
  }
}

export const api = new ApiService();
export default api;
