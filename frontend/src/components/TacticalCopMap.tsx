/**
 * ShiVi Operations Console - Common Operational Picture (COP) Tactical Map
 * ========================================================================
 *
 * Briefing:
 *     Vector-based tactical radar and geospatial situational map component (`TacticalCopMap`).
 *     Projects WGS84 geographic coordinates (EPSG:4326) onto an interactive SVG viewport
 *     (1000x650 coordinate canvas) centered on Guwahati Sector 4 disaster operations.
 *     Renders multiple toggleable tactical layers:
 *     - Brahmaputra river waterway geometry and live flood surge inundation polygon.
 *     - Evacuation and transit corridors, prominently highlighting safety-frozen routes (e.g. Route-88).
 *     - Critical civilian infrastructure (hospitals, relief shelters, boat ramps).
 *     - Real-time field responder telemetry (SDRF rescue boats, aerial reconnaissance drones).
 *     - Pulsing incident radar pins colored by severity with explainable priority tags.
 *
 * Reason:
 *     In disaster scenarios, third-party vector tile services (Mapbox, Google Maps) fail
 *     during cellular blackouts or when bandwidth drops to 1-2 kbps over tactical mesh radios.
 *     An embedded, zero-dependency SVG tactical radar guarantees instant rendering, offline durability,
 *     and clear visual distinction of life-safety causal freezes without relying on external internet tiles.
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  Layers,
  MapPin,
  Lock,
  Radio,
  Crosshair,
  AlertTriangle,
  Droplets,
  Shield,
  Navigation,
  LifeBuoy,
  Plus,
  Minus,
  Maximize2,
  RefreshCw,
} from "lucide-react";
import { IncidentItem, TacticalMapData } from "../services/api";

/**
 * Briefing:
 *     Component properties configuring tactical radar display and event callbacks.
 */
interface TacticalCopMapProps {
  // Explanation: List of active disaster incidents to plot as radar pins.
  incidents: IncidentItem[];
  // Explanation: UUID of currently highlighted incident in the COP feed.
  selectedIncidentId: string | null;
  // Explanation: Callback fired when operator clicks an incident pin on the radar.
  onSelectIncident: (id: string) => void;
  // Explanation: Dynamic spatial and hydrological layers from backend /v1/dashboard/map-layers.
  mapData?: TacticalMapData | null;
  // Explanation: Invariant flag indicating whether Route-88 is currently under causal safety freeze.
  isRouteFrozen?: boolean;
}

/**
 * Briefing:
 *     Interactive SVG Tactical COP Map component.
 *
 * Reason:
 *     Renders a high-contrast dark-mode tactical overview with pan, zoom, and layer toggling,
 *     ensuring rapid situational awareness under extreme operational stress.
 *
 * @param props TacticalCopMapProps configuration and callbacks.
 */
export default function TacticalCopMap({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  mapData,
  isRouteFrozen = true,
}: TacticalCopMapProps) {
  // Explanation: Toggle state for the hydrological flood surge polygon overlay.
  const [showFloodPolygon, setShowFloodPolygon] = useState(true);
  // Explanation: Toggle state for evacuation routes and transit corridors.
  const [showRoutes, setShowRoutes] = useState(true);
  // Explanation: Toggle state for active field responders and aerial drones.
  const [showUnits, setShowUnits] = useState(true);
  // Explanation: Toggle state for fixed infrastructure (hospitals, shelters, ramps).
  const [showInfrastructure, setShowInfrastructure] = useState(true);
  // Explanation: Zoom magnification factor for the SVG canvas (range 0.85 to 1.4).
  const [zoomLevel, setZoomLevel] = useState(1);
  // Explanation: ID of feature currently hovered or focused by the operator.
  const [activeHoverId, setActiveHoverId] = useState<string | null>(null);

  // Geographic bounds for Guwahati Sector 4 mapping to SVG viewBox (0 0 1000 650)
  // Lat: 26.1400 to 26.2100 (~0.07 deg range)
  // Lng: 91.7000 to 91.8000 (~0.10 deg range)
  const minLat = 26.1400;
  const maxLat = 26.2100;
  const minLng = 91.7000;
  const maxLng = 91.8000;

  /**
   * Briefing:
   *     Linear geographic projection converting WGS-84 coordinates to SVG pixel space.
   *
   * Reason:
   *     Provides deterministic, zero-dependency translation from latitude/longitude
   *     to viewport coordinates (X: 0..1000, Y: 0..650).
   *
   * @param lat WGS-84 latitude.
   * @param lng WGS-84 longitude.
   * @returns Projected SVG coordinate object { x, y }.
   */
  const project = (lat: number, lng: number) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * 1000;
    const y = ((maxLat - lat) / (maxLat - minLat)) * 650;
    return { x, y };
  };

  // Explanation: Pre-calculated Bézier curve path for Brahmaputra river waterway traversing the sector.
  const riverPath =
    "M 0,220 C 180,240 320,180 500,230 C 680,280 820,220 1000,260 L 1000,420 C 820,380 660,430 480,390 C 300,350 160,410 0,380 Z";

  // Explanation: Inundation flood surge zone polygon point string, derived from live telemetry or offline fallback.
  const floodPolygonPoints = mapData?.inundation_polygon
    ? mapData.inundation_polygon.map((p) => `${project(p.lat, p.lng).x},${project(p.lat, p.lng).y}`).join(" ")
    : "180,220 750,230 850,480 320,510 120,380";

  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm relative flex flex-col">
      {/* HUD Header Bar */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-amber-600 animate-spin" style={{ animationDuration: "12s" }} />
            <span className="font-bold text-slate-900 tracking-wider uppercase font-mono">
              Tactical COP Radar // Sector 4
            </span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
            WGS84 EPSG:4326
          </span>
          {isRouteFrozen && (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 flex items-center gap-1 animate-pulse">
              <Lock className="w-2.5 h-2.5" /> ROUTE-88 FROZEN
            </span>
          )}
        </div>

        {/* Layer Toggles */}
        <div className="flex items-center gap-2 text-[11px]">
          <button
            onClick={() => setShowFloodPolygon(!showFloodPolygon)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showFloodPolygon
                ? "bg-red-50 border-red-200 text-red-700 font-bold shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Droplets className="w-3 h-3 text-red-600" /> Flood Surge
          </button>

          <button
            onClick={() => setShowRoutes(!showRoutes)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showRoutes
                ? "bg-amber-50 border-amber-200 text-amber-800 font-bold shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Navigation className="w-3 h-3 text-amber-600" /> Corridors
          </button>

          <button
            onClick={() => setShowUnits(!showUnits)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showUnits
                ? "bg-orange-50 border-orange-200 text-orange-800 font-bold shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Radio className="w-3 h-3 text-orange-600" /> Responders
          </button>

          <button
            onClick={() => setShowInfrastructure(!showInfrastructure)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showInfrastructure
                ? "bg-emerald-50 border-emerald-200 text-emerald-700 font-bold shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Shield className="w-3 h-3 text-emerald-600" /> Shelters/Hospitals
          </button>

          <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
            <button
              onClick={() => setZoomLevel((z) => Math.min(z + 0.15, 1.4))}
              className="p-1 rounded hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoomLevel((z) => Math.max(z - 0.15, 0.85))}
              className="p-1 rounded hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-all"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main SVG Radar Canvas */}
      <div className="relative w-full aspect-[16/9] max-h-[520px] bg-slate-50 overflow-hidden select-none border-t border-slate-200">
        <svg
          viewBox="0 0 1000 650"
          className="w-full h-full transition-transform duration-300 ease-out"
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center" }}
        >
          <defs>
            {/* Grid Pattern */}
            <pattern id="tacticalGrid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#E2E8F0" strokeWidth="0.8" />
            </pattern>

            {/* Inundation Striped Pattern */}
            <pattern id="floodHatch" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="12" stroke="#DC2626" strokeWidth="2.5" strokeOpacity="0.22" />
            </pattern>

            {/* Gradients */}
            <linearGradient id="riverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#BAE6FD" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#93C5FD" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#BAE6FD" stopOpacity="0.7" />
            </linearGradient>

            <radialGradient id="freezePulse" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#EF4444" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#EF4444" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background Cartographic Fill & Grid */}
          <rect width="1000" height="650" fill="#F8FAFC" />
          <rect width="1000" height="650" fill="url(#tacticalGrid)" />

          {/* River Brahmaputra Body */}
          <path d={riverPath} fill="url(#riverGrad)" stroke="#0284C7" strokeWidth="1.5" />
          <text x="360" y="320" fill="#0369A1" fillOpacity="0.5" fontSize="16" fontWeight="bold" letterSpacing="4">
            BRAHMAPUTRA RIVER WATERWAY
          </text>

          {/* Flood Inundation Polygon Layer */}
          {showFloodPolygon && (
            <g>
              <polygon points={floodPolygonPoints} fill="url(#floodHatch)" stroke="#DC2626" strokeWidth="2" strokeDasharray="6 4" />
              <text x="460" y="470" fill="#B91C1C" fontSize="11" fontWeight="bold" letterSpacing="1.5">
                ACTIVE FLOOD SURGE ZONE (+2.45m)
              </text>
            </g>
          )}

          {/* Route Corridors Layer */}
          {showRoutes && (
            <g>
              {/* Route-88 (Sector 4 Main Bridge) */}
              <g className="cursor-pointer" onClick={() => setActiveHoverId("ROUTE-88")}>
                <line
                  x1="480"
                  y1="220"
                  x2="520"
                  y2="400"
                  stroke={isRouteFrozen ? "#DC2626" : "#16A34A"}
                  strokeWidth="6"
                  strokeDasharray={isRouteFrozen ? "8 4" : "none"}
                />
                {isRouteFrozen && (
                  <circle cx="500" cy="310" r="22" fill="url(#freezePulse)" className="animate-ping" />
                )}
                <rect
                  x="455"
                  y="295"
                  width="90"
                  height="26"
                  rx="6"
                  fill="#FFFFFF"
                  stroke={isRouteFrozen ? "#DC2626" : "#16A34A"}
                  strokeWidth="1.5"
                />
                <text
                  x="500"
                  y="312"
                  textAnchor="middle"
                  fill={isRouteFrozen ? "#991B1B" : "#166534"}
                  fontSize="10"
                  fontWeight="bold"
                >
                  {isRouteFrozen ? "ROUTE-88 [FROZEN]" : "ROUTE-88 [OPEN]"}
                </text>
              </g>

              {/* Route-4B (Shallow Water Boat Ramp Bypass) */}
              <g>
                <path d="M 380,240 Q 320,330 360,450" fill="none" stroke="#D97706" strokeWidth="3.5" strokeDasharray="4 2" />
                <rect x="290" y="340" width="80" height="20" rx="4" fill="#FFFFFF" stroke="#D97706" strokeWidth="1" />
                <text x="330" y="354" textAnchor="middle" fill="#B45309" fontSize="9" fontWeight="bold">
                  ROUTE-4B (BOAT)
                </text>
              </g>

              {/* North Elevated Ring Road Bypass */}
              <g>
                <path d="M 100,120 Q 500,80 900,140" fill="none" stroke="#16A34A" strokeWidth="3" opacity="0.8" />
                <text x="500" y="95" textAnchor="middle" fill="#15803D" fontSize="10" fontWeight="bold">
                  NORTH ELEVATED BYPASS (CLEAR)
                </text>
              </g>
            </g>
          )}

          {/* Critical Infrastructure Layer */}
          {showInfrastructure && (
            <g>
              {/* GMCH Hospital */}
              <g transform="translate(720, 520)">
                <circle cx="0" cy="0" r="14" fill="#FFFFFF" stroke="#D97706" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#B45309" fontSize="10" fontWeight="bold">
                  GMCH
                </text>
                <rect x="-65" y="18" width="130" height="18" rx="4" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#334155" fontSize="9" fontWeight="medium">
                  Hospital (38 Beds Avail)
                </text>
              </g>

              {/* Relief Camp #3 */}
              <g transform="translate(240, 150)">
                <circle cx="0" cy="0" r="14" fill="#FFFFFF" stroke="#16A34A" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#15803D" fontSize="10" fontWeight="bold">
                  RC-3
                </text>
                <rect x="-60" y="18" width="120" height="18" rx="4" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#166534" fontSize="9" fontWeight="medium">
                  Relief Camp (320/500)
                </text>
              </g>

              {/* Pandu Port Inflatable Boat Landing Ramp */}
              <g transform="translate(190, 420)">
                <circle cx="0" cy="0" r="14" fill="#FFFFFF" stroke="#EA580C" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#C2410C" fontSize="10" fontWeight="bold">
                  RAMP
                </text>
                <rect x="-60" y="18" width="120" height="18" rx="4" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#9A3412" fontSize="9" fontWeight="medium">
                  Boat Staging (6 Boats)
                </text>
              </g>
            </g>
          )}

          {/* Responder Units Layer */}
          {showUnits && (
            <g>
              {/* SDRF Rescue Unit Alpha (IRB Boat 04) */}
              <g transform="translate(430, 360)">
                <circle cx="0" cy="0" r="16" fill="#FFEDD5" stroke="#EA580C" strokeWidth="2" />
                <polygon points="0,-8 6,6 -6,6" fill="#EA580C" />
                <rect x="-60" y="20" width="120" height="18" rx="4" fill="#FFFFFF" stroke="#EA580C" strokeWidth="1" />
                <text x="0" y="32" textAnchor="middle" fill="#9A3412" fontSize="9" fontWeight="bold">
                  SDRF Boat-04 (87% Bat)
                </text>
              </g>

              {/* Drone Alpha */}
              <g transform="translate(560, 260)">
                <circle cx="0" cy="0" r="12" fill="#FEF3C7" stroke="#D97706" strokeWidth="1.5" />
                <text x="0" y="3" textAnchor="middle" fill="#92400E" fontSize="8" fontWeight="bold">
                  UAV
                </text>
                <circle cx="0" cy="0" r="28" fill="none" stroke="#D97706" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                <rect x="-50" y="16" width="100" height="16" rx="4" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1" />
                <text x="0" y="28" textAnchor="middle" fill="#475569" fontSize="8" fontWeight="medium">
                  Recon Drone (120m)
                </text>
              </g>
            </g>
          )}

          {/* Incidents Layer (Pulsing radar pins) */}
          {incidents.map((inc) => {
            const pos = project(inc.latitude, inc.longitude);
            const isSelected = selectedIncidentId === inc.id;
            const isCritical = inc.severity === "CRITICAL";

            return (
              <g
                key={inc.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer group"
                onClick={() => onSelectIncident(inc.id)}
              >
                {/* Pulsing Ripple */}
                <circle
                  cx="0"
                  cy="0"
                  r={isSelected ? "26" : "18"}
                  fill={isCritical ? "#DC2626" : "#D97706"}
                  opacity="0.2"
                  className="animate-ping"
                />

                {/* Outer Target Circle */}
                <circle
                  cx="0"
                  cy="0"
                  r={isSelected ? "14" : "10"}
                  fill="#FFFFFF"
                  stroke={isCritical ? "#DC2626" : "#D97706"}
                  strokeWidth={isSelected ? "3" : "2"}
                />

                {/* Inner Core */}
                <circle
                  cx="0"
                  cy="0"
                  r={isSelected ? "6" : "4"}
                  fill={isCritical ? "#DC2626" : "#D97706"}
                />

                {/* Pin Label Tag */}
                <rect
                  x="-75"
                  y="-34"
                  width="150"
                  height="22"
                  rx="6"
                  fill="#FFFFFF"
                  stroke={isSelected ? "#D97706" : "#CBD5E1"}
                  strokeWidth={isSelected ? "2" : "1"}
                  className="transition-all shadow-sm"
                />
                <text
                  x="0"
                  y="-20"
                  textAnchor="middle"
                  fill="#0F172A"
                  fontSize="9.5"
                  fontWeight="bold"
                >
                  P{inc.priority_score.toFixed(0)} | {inc.title.slice(0, 18)}...
                </text>
              </g>
            );
          })}
        </svg>

        {/* Bottom HUD Telemetry Overlay */}
        <div className="absolute bottom-3 left-3 right-3 bg-white/95 border border-slate-200 rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-red-700 font-semibold">
              <Droplets className="w-3.5 h-3.5 animate-bounce" />
              <span>FLOOD SURGE: +2.45m</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-800 font-semibold">
              <Compass className="w-3.5 h-3.5" />
              <span>VELOCITY: 3.8 m/s</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-800 font-semibold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>TREND: RISING (+0.15m/hr)</span>
            </div>
          </div>

          <div className="text-[11px] text-slate-500 flex items-center gap-2 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>GEO-RADAR REFRESH: REALTIME (BLE/MESH)</span>
          </div>
        </div>
      </div>
    </div>

  );
}
