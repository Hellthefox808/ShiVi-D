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

interface TacticalCopMapProps {
  incidents: IncidentItem[];
  selectedIncidentId: string | null;
  onSelectIncident: (id: string) => void;
  mapData?: TacticalMapData | null;
  isRouteFrozen?: boolean;
}

export default function TacticalCopMap({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  mapData,
  isRouteFrozen = true,
}: TacticalCopMapProps) {
  const [showFloodPolygon, setShowFloodPolygon] = useState(true);
  const [showRoutes, setShowRoutes] = useState(true);
  const [showUnits, setShowUnits] = useState(true);
  const [showInfrastructure, setShowInfrastructure] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [activeHoverId, setActiveHoverId] = useState<string | null>(null);

  // Geographic bounds for Guwahati Sector 4 mapping to SVG viewBox (0 0 1000 650)
  // Lat: 26.1400 to 26.2100 (~0.07 deg range)
  // Lng: 91.7000 to 91.8000 (~0.10 deg range)
  const minLat = 26.1400;
  const maxLat = 26.2100;
  const minLng = 91.7000;
  const maxLng = 91.8000;

  const project = (lat: number, lng: number) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * 1000;
    const y = ((maxLat - lat) / (maxLat - minLat)) * 650;
    return { x, y };
  };

  // Pre-calculated river path for Brahmaputra through the sector
  const riverPath =
    "M 0,220 C 180,240 320,180 500,230 C 680,280 820,220 1000,260 L 1000,420 C 820,380 660,430 480,390 C 300,350 160,410 0,380 Z";

  // Inundation flood surge zone polygon
  const floodPolygonPoints = mapData?.inundation_polygon
    ? mapData.inundation_polygon.map((p) => `${project(p.lat, p.lng).x},${project(p.lat, p.lng).y}`).join(" ")
    : "180,220 750,230 850,480 320,510 120,380";

  return (
    <div className="bg-[#121826] border border-[#1E293B] rounded-2xl overflow-hidden shadow-2xl relative flex flex-col">
      {/* HUD Header Bar */}
      <div className="bg-[#0B0F19]/90 border-b border-[#1E293B] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-blue-400 animate-spin" style={{ animationDuration: "12s" }} />
            <span className="font-bold text-white tracking-wider uppercase font-mono">
              Tactical COP Radar // Sector 4
            </span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
            WGS84 EPSG:4326
          </span>
          {isRouteFrozen && (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1 animate-pulse">
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
                ? "bg-red-500/20 border-red-500/40 text-red-300 font-semibold"
                : "bg-gray-800/40 border-gray-700 text-gray-400"
            }`}
          >
            <Droplets className="w-3 h-3" /> Flood Surge
          </button>

          <button
            onClick={() => setShowRoutes(!showRoutes)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showRoutes
                ? "bg-amber-500/20 border-amber-500/40 text-amber-300 font-semibold"
                : "bg-gray-800/40 border-gray-700 text-gray-400"
            }`}
          >
            <Navigation className="w-3 h-3" /> Corridors
          </button>

          <button
            onClick={() => setShowUnits(!showUnits)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showUnits
                ? "bg-blue-500/20 border-blue-500/40 text-blue-300 font-semibold"
                : "bg-gray-800/40 border-gray-700 text-gray-400"
            }`}
          >
            <Radio className="w-3 h-3" /> Responders
          </button>

          <button
            onClick={() => setShowInfrastructure(!showInfrastructure)}
            className={`px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1 ${
              showInfrastructure
                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300 font-semibold"
                : "bg-gray-800/40 border-gray-700 text-gray-400"
            }`}
          >
            <Shield className="w-3 h-3" /> Shelters/Hospitals
          </button>

          <div className="flex items-center gap-1 pl-2 border-l border-gray-800">
            <button
              onClick={() => setZoomLevel((z) => Math.min(z + 0.15, 1.4))}
              className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoomLevel((z) => Math.max(z - 0.15, 0.85))}
              className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main SVG Radar Canvas */}
      <div className="relative w-full aspect-[16/9] max-h-[520px] bg-[#070A12] overflow-hidden select-none">
        <svg
          viewBox="0 0 1000 650"
          className="w-full h-full transition-transform duration-300 ease-out"
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center" }}
        >
          <defs>
            {/* Grid Pattern */}
            <pattern id="tacticalGrid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#1E293B" strokeWidth="0.5" strokeOpacity="0.6" />
            </pattern>

            {/* Inundation Striped Pattern */}
            <pattern id="floodHatch" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="12" stroke="#EF4444" strokeWidth="2.5" strokeOpacity="0.35" />
            </pattern>

            {/* Gradients */}
            <linearGradient id="riverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0E3A5A" stopOpacity="0.7" />
              <stop offset="50%" stopColor="#0B2545" stopOpacity="0.85" />
              <stop offset="100%" stopColor="#0E3A5A" stopOpacity="0.7" />
            </linearGradient>

            <radialGradient id="freezePulse" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#EF4444" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#EF4444" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background Coordinate Grid */}
          <rect width="1000" height="650" fill="url(#tacticalGrid)" />

          {/* River Brahmaputra Body */}
          <path d={riverPath} fill="url(#riverGrad)" stroke="#1E4E7A" strokeWidth="1.5" />
          <text x="360" y="320" fill="#38BDF8" fillOpacity="0.35" fontSize="18" fontWeight="bold" letterSpacing="4">
            BRAHMAPUTRA RIVER WATERWAY
          </text>

          {/* Flood Inundation Polygon Layer */}
          {showFloodPolygon && (
            <g>
              <polygon points={floodPolygonPoints} fill="url(#floodHatch)" stroke="#EF4444" strokeWidth="2" strokeDasharray="6 4" />
              <text x="460" y="470" fill="#EF4444" fontSize="11" fontWeight="bold" letterSpacing="1.5">
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
                  stroke={isRouteFrozen ? "#EF4444" : "#10B981"}
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
                  fill="#0B0F19"
                  stroke={isRouteFrozen ? "#EF4444" : "#10B981"}
                  strokeWidth="1.5"
                />
                <text
                  x="500"
                  y="312"
                  textAnchor="middle"
                  fill={isRouteFrozen ? "#F87171" : "#34D399"}
                  fontSize="10"
                  fontWeight="bold"
                >
                  {isRouteFrozen ? "ROUTE-88 [FROZEN]" : "ROUTE-88 [OPEN]"}
                </text>
              </g>

              {/* Route-4B (Shallow Water Boat Ramp Bypass) */}
              <g>
                <path d="M 380,240 Q 320,330 360,450" fill="none" stroke="#06B6D4" strokeWidth="3.5" strokeDasharray="4 2" />
                <rect x="290" y="340" width="80" height="20" rx="4" fill="#0B0F19" stroke="#06B6D4" strokeWidth="1" />
                <text x="330" y="354" textAnchor="middle" fill="#22D3EE" fontSize="9" fontWeight="bold">
                  ROUTE-4B (BOAT)
                </text>
              </g>

              {/* North Elevated Ring Road Bypass */}
              <g>
                <path d="M 100,120 Q 500,80 900,140" fill="none" stroke="#10B981" strokeWidth="3" opacity="0.8" />
                <text x="500" y="95" textAnchor="middle" fill="#34D399" fontSize="10" fontWeight="bold">
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
                <circle cx="0" cy="0" r="14" fill="#0B0F19" stroke="#3B82F6" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#60A5FA" fontSize="10" fontWeight="bold">
                  GMCH
                </text>
                <rect x="-65" y="18" width="130" height="18" rx="4" fill="#0B0F19" stroke="#1E293B" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#93C5FD" fontSize="9">
                  Hospital (38 Beds Avail)
                </text>
              </g>

              {/* Relief Camp #3 */}
              <g transform="translate(240, 150)">
                <circle cx="0" cy="0" r="14" fill="#0B0F19" stroke="#10B981" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#34D399" fontSize="10" fontWeight="bold">
                  RC-3
                </text>
                <rect x="-60" y="18" width="120" height="18" rx="4" fill="#0B0F19" stroke="#1E293B" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#A7F3D0" fontSize="9">
                  Relief Camp (320/500)
                </text>
              </g>

              {/* Pandu Port Inflatable Boat Landing Ramp */}
              <g transform="translate(190, 420)">
                <circle cx="0" cy="0" r="14" fill="#0B0F19" stroke="#F59E0B" strokeWidth="2" />
                <text x="0" y="4" textAnchor="middle" fill="#FBBF24" fontSize="10" fontWeight="bold">
                  RAMP
                </text>
                <rect x="-60" y="18" width="120" height="18" rx="4" fill="#0B0F19" stroke="#1E293B" strokeWidth="1" />
                <text x="0" y="30" textAnchor="middle" fill="#FDE68A" fontSize="9">
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
                <circle cx="0" cy="0" r="16" fill="#1E3A8A" stroke="#3B82F6" strokeWidth="2" />
                <polygon points="0,-8 6,6 -6,6" fill="#60A5FA" />
                <rect x="-60" y="20" width="120" height="18" rx="4" fill="#0B0F19" stroke="#3B82F6" strokeWidth="1" />
                <text x="0" y="32" textAnchor="middle" fill="#93C5FD" fontSize="9" fontWeight="bold">
                  SDRF Boat-04 (87% Bat)
                </text>
              </g>

              {/* Drone Alpha */}
              <g transform="translate(560, 260)">
                <circle cx="0" cy="0" r="12" fill="#312E81" stroke="#818CF8" strokeWidth="1.5" />
                <text x="0" y="3" textAnchor="middle" fill="#C7D2FE" fontSize="8" fontWeight="bold">
                  UAV
                </text>
                <circle cx="0" cy="0" r="28" fill="none" stroke="#818CF8" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                <rect x="-50" y="16" width="100" height="16" rx="4" fill="#0B0F19" stroke="#1E293B" strokeWidth="1" />
                <text x="0" y="28" textAnchor="middle" fill="#E0E7FF" fontSize="8">
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
                  fill={isCritical ? "#EF4444" : "#F59E0B"}
                  opacity="0.25"
                  className="animate-ping"
                />

                {/* Outer Target Circle */}
                <circle
                  cx="0"
                  cy="0"
                  r={isSelected ? "14" : "10"}
                  fill="#0B0F19"
                  stroke={isCritical ? "#EF4444" : "#F59E0B"}
                  strokeWidth={isSelected ? "3" : "2"}
                />

                {/* Inner Core */}
                <circle
                  cx="0"
                  cy="0"
                  r={isSelected ? "6" : "4"}
                  fill={isCritical ? "#EF4444" : "#F59E0B"}
                />

                {/* Pin Label Tag */}
                <rect
                  x="-75"
                  y="-34"
                  width="150"
                  height="22"
                  rx="6"
                  fill="#0B0F19"
                  stroke={isSelected ? "#3B82F6" : "#1E293B"}
                  strokeWidth={isSelected ? "2" : "1"}
                  className="transition-all"
                />
                <text
                  x="0"
                  y="-20"
                  textAnchor="middle"
                  fill="#FFFFFF"
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
        <div className="absolute bottom-3 left-3 right-3 bg-[#0B0F19]/90 border border-[#1E293B] rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-xs font-mono backdrop-blur-md">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-red-400">
              <Droplets className="w-3.5 h-3.5 animate-bounce" />
              <span>FLOOD SURGE: +2.45m</span>
            </div>
            <div className="flex items-center gap-1.5 text-blue-300">
              <Compass className="w-3.5 h-3.5" />
              <span>VELOCITY: 3.8 m/s</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-300">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>TREND: RISING (+0.15m/hr)</span>
            </div>
          </div>

          <div className="text-[11px] text-gray-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>GEO-RADAR REFRESH: REALTIME (BLE/MESH)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
