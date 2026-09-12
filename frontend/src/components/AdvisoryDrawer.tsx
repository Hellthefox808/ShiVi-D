/**
 * ShiVi Operations Console - Governed Multimodal AI Advisory Studio
 * ===================================================================
 *
 * Briefing:
 *     Slide-out drawer component (`AIAdvisoryDrawer`) implementing the ShiVi
 *     "Governed Advisory AI" invariant (Invariant 5).
 *     Provides interactive AI-assisted triage capabilities:
 *     - Multilingual emergency dispatch presets (Hindi, Assamese, English) matching regional disaster patterns.
 *     - Simulated audio waveform visualizer and speech-to-text transcription engine.
 *     - Structured disaster entity extraction (hazard category, severity, people at risk).
 *     - Explainable multi-factor priority score calculation ($P \in [0, 100]$).
 *     - NDMA Standard Operating Procedure (SOP) retrieval with mandatory safety checklists.
 *     - Explicit human commander authorization before any extracted values can be applied to canonical state.
 *
 * Reason:
 *     Autonomous AI decision-making without supervision in life-safety environments creates legal and ethical
 *     catastrophes (hallucinated boat assignments, miscategorized casualties). In ShiVi, AI is strictly advisory:
 *     models propose extractions and SOP checklists, but only certified human incident commanders can authorize
 *     and apply the results to the mission database.
 */

"use client";

import React, { useState } from "react";
import {
  Sparkles,
  X,
  Send,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Mic,
  Volume2,
  Play,
  RotateCcw,
} from "lucide-react";
import api, { VoiceTriageResponse } from "../services/api";

/**
 * Briefing:
 *     Component properties controlling drawer visibility and callback actions.
 */
interface AIAdvisoryDrawerProps {
  // Explanation: True if the slide-out drawer is open.
  isOpen: boolean;
  // Explanation: Handler to close the drawer.
  onClose: () => void;
  // Explanation: Callback fired when operator authorizes and applies extracted values to the active incident.
  onApplyExtraction: (extracted: any) => void;
}

/**
 * Briefing:
 *     Governed Multimodal AI Advisory Drawer component.
 *
 * Reason:
 *     Provides commanders with an on-demand AI copilot to parse messy incoming voice and text reports,
 *     compute explainable urgency ratings, and pull NDMA SOP checklists without relinquishing control.
 *
 * @param props AIAdvisoryDrawerProps configuration.
 */
export function AIAdvisoryDrawer({
  isOpen,
  onClose,
  onApplyExtraction,
}: AIAdvisoryDrawerProps) {
  // Explanation: Selected language code for speech transcription ('hi', 'as', 'en').
  const [selectedLanguage, setSelectedLanguage] = useState<"hi" | "as" | "en">("hi");
  // Explanation: Raw input field transcript or distress message text.
  const [inputText, setInputText] = useState<string>(
    "वार्ड 4 में ब्रह्मपुत्र का पानी घरों में घुस रहा है, 5 लोग छत पर फंसे हैं, तुरंत मोटरबोट भेजो!"
  );
  // Explanation: True while backend AI model is transcribing and extracting entities.
  const [isVoiceProcessing, setIsVoiceProcessing] = useState<boolean>(false);
  // Explanation: Structured triage response returned by /v1/ai/voice-triage.
  const [voiceResult, setVoiceResult] = useState<VoiceTriageResponse | null>(null);
  // Explanation: Visual animation state for the simulated audio waveform bars.
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  // Explanation: Return null if drawer is closed to minimize DOM overhead.
  if (!isOpen) return null;

  // Explanation: Realistic regional disaster distress report presets.
  const samplePresets = {
    hi: {
      label: "Hindi Audio",
      text: "वार्ड 4 में ब्रह्मपुत्र का पानी घरों में घुस रहा है, 5 लोग छत पर फंसे हैं, तुरंत मोटरबोट भेजो!",
    },
    as: {
      label: "Assamese Audio",
      text: "ব্ৰহ্মপুত্ৰৰ পানী বৃদ্ধি পাইছে, ৪ নম্বৰ ৱাৰ্ডত আমাৰ ঘৰ ডুব গৈছে, সহায় লাগে!",
    },
    en: {
      label: "English Audio",
      text: "Critical flash flood surge near Sector 4 Bridge, 3 civilians stranded on hospital roof, urgent boat needed.",
    },
  };

  /**
   * Briefing:
   *     Switches active language preset and populates sample distress transcript.
   *
   * @param lang Language identifier ('hi', 'as', 'en').
   */
  const handleSelectPreset = (lang: "hi" | "as" | "en") => {
    setSelectedLanguage(lang);
    setInputText(samplePresets[lang].text);
  };

  /**
   * Briefing:
   *     Dispatches input text to backend multimodal voice triage endpoint.
   *
   * Reason:
   *     Triggers transcription animation, queries /v1/ai/voice-triage, and stores
   *     structured extraction, urgency breakdown, and NDMA SOP recommendations in local state.
   */
  const handleRunVoiceTriage = async () => {
    setIsVoiceProcessing(true);
    setIsPlayingAudio(true);
    setTimeout(() => setIsPlayingAudio(false), 1200);

    try {
      const res = await api.voiceTriage(inputText, selectedLanguage);
      setVoiceResult(res);
    } catch (err) {
      console.error("Voice triage error:", err);
    } finally {
      setIsVoiceProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white border-l border-slate-200 w-full max-w-xl h-full flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                Governed Multimodal AI Advisory Studio
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                  INVARIANT 5
                </span>
              </h3>
              <p className="text-xs text-slate-600">
                Confidence-bounded AI suggestions with mandatory human commander authorization
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Audio Waveform Simulator */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Mic className="w-4 h-4 text-amber-600" /> Multilingual Voice Emergency Dispatch
              </span>
              <span className="text-[10px] font-mono text-amber-800 font-bold">WHISPER-V3 COMPATIBLE</span>
            </div>

            {/* Language Preset Tabs */}
            <div className="flex gap-2">
              {(["hi", "as", "en"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => handleSelectPreset(lang)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                    selectedLanguage === lang
                      ? "bg-amber-500 border-amber-500 text-white font-bold shadow-md shadow-amber-500/20"
                      : "bg-white border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {samplePresets[lang].label}
                </button>
              ))}
            </div>

            {/* Audio Wave Graphic */}
            <div className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-3 shadow-sm">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all ${
                  isPlayingAudio ? "bg-amber-500 text-white animate-pulse font-bold" : "bg-amber-100 text-amber-700"
                }`}
              >
                <Volume2 className="w-5 h-5" />
              </div>

              {/* Simulated Waveform Bars */}
              <div className="flex items-center gap-1 flex-1 h-8">
                {[40, 75, 30, 90, 60, 100, 45, 80, 55, 95, 30, 85, 70, 40, 90, 60, 75, 50, 85, 60, 40].map(
                  (h, i) => (
                    <div
                      key={i}
                      className={`flex-1 rounded-full transition-all ${
                        isPlayingAudio ? "bg-amber-500 animate-pulse" : "bg-slate-200"
                      }`}
                      style={{ height: `${isPlayingAudio ? Math.max(20, (h * Math.random() + 20)) : h}%` }}
                    />
                  )
                )}
              </div>
            </div>

            {/* Transcript Area */}
            <textarea
              rows={3}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-amber-500 transition-all font-mono"
            />

            {/* Action Button */}
            <button
              onClick={handleRunVoiceTriage}
              disabled={isVoiceProcessing || !inputText.trim()}
              className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
            >
              {isVoiceProcessing ? (
                <RotateCcw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
              <span>Transcribe & Extract Structured Triage</span>
            </button>
          </div>

          {/* Structured Output & Explainable Priority Display */}
          {voiceResult && (
            <div className="bg-slate-50 border border-amber-200 rounded-2xl p-5 space-y-4 shadow-sm animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Advisory Triage Result
                </span>
                <span className="text-[10px] font-mono text-slate-500">
                  Latency: {voiceResult.transcription_latency_ms} ms • Hash: {voiceResult.prompt_hash}
                </span>
              </div>

              {/* Extraction Metrics */}
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-white p-2.5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Category</span>
                  <span className="text-xs font-bold text-slate-900">{voiceResult.extraction.category}</span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">Severity</span>
                  <span className="text-xs font-bold text-red-600">{voiceResult.extraction.severity}</span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 uppercase block font-semibold">People at Risk</span>
                  <span className="text-xs font-bold text-amber-700">{voiceResult.extraction.estimated_people}</span>
                </div>
              </div>

              {/* Explainable Priority Score */}
              <div className="bg-white p-3.5 rounded-xl border border-amber-200 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Explainable Multi-Factor Priority</span>
                  <span className="text-sm font-black text-amber-700">
                    {voiceResult.urgency_score} / 100
                  </span>
                </div>
                {voiceResult.urgency_breakdown.explanation && (
                  <p className="text-[11px] text-slate-600 italic">
                    "{voiceResult.urgency_breakdown.explanation}"
                  </p>
                )}
              </div>

              {/* Official SOP Recommendation */}
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">
                    {voiceResult.recommended_sop.title}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {voiceResult.recommended_sop.sop_code}
                  </span>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">
                    Mandatory Checklist:
                  </span>
                  <ul className="space-y-1 text-[11px] text-slate-700">
                    {voiceResult.recommended_sop.mandatory_checklist.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Apply to Active Incident Button */}
              <button
                onClick={() => {
                  onApplyExtraction({
                    category: voiceResult.extraction.category,
                    severity: voiceResult.extraction.severity,
                    people_at_risk: voiceResult.extraction.estimated_people,
                  });
                  onClose();
                }}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-600/20"
              >
                <FileCheck className="w-4 h-4" />
                <span>Apply Extracted Values to Incident State</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIAdvisoryDrawer;
