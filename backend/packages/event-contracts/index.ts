/**
 * ShiVi Operational Event Contracts - TypeScript Definition
 * Strict Causal Envelope for Offline-First Synchronization
 */

export type EntityType =
  | 'incident'
  | 'task'
  | 'assignment'
  | 'resource'
  | 'route_observation'
  | 'conflict_case'
  | 'verification';

export interface FieldChange<T = unknown> {
  base?: T;
  new: T;
}

export interface ShiViOperationalEventEnvelope {
  event_id: string;
  tenant_id: string;
  entity_type: EntityType;
  entity_id: string;
  event_type: string;
  changes: Record<string, FieldChange>;
  actor_id: string;
  device_id: string;
  device_sequence: number;
  occurred_at: string; // ISO-8601 UTC
  version_vector: Record<string, number>;
  evidence_ids?: string[];
  schema_version: 1;
  integrity_hash: string; // 64-character SHA-256 Hex Digest
}

export interface SyncPushBatch {
  device_id: string;
  events: ShiViOperationalEventEnvelope[];
}

export interface SyncPushResult {
  status: 'success' | 'partial' | 'error';
  processed_count: number;
  accepted_event_ids: string[];
  duplicate_event_ids: string[];
  conflicts_detected: number;
  server_cursor: string;
}

export interface SyncPullResult {
  events: Array<{
    event_id: string;
    entity_type: EntityType;
    entity_id: string;
    event_type: string;
    changes: Record<string, FieldChange>;
    actor_id: string;
    device_id: string;
    occurred_at: string;
    received_at: string;
    evidence_ids?: string[];
    integrity_hash: string;
  }>;
  next_cursor: string;
  has_more: boolean;
}
