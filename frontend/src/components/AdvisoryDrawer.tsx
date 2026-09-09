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

interface AIAdvisoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyExtraction: (extracted: any) => void;
}

export function AIAdvisoryDrawer({
  isOpen,
  onClose,
  onApplyExtraction,
}: AIAdvisoryDrawerProps) {
  const [selectedLanguage, setSelectedLanguage] = useState<"hi" | "as" | "en">("hi");
  const [inputText, setInputText] = useState<string>(
    "वार्ड 4 में ब्रह्मपुत्र का पानी घरों में घुस रहा है, 5 लोग छत पर फंसे हैं, तुरंत मोटरबोट भेजो!"
  );
  const [isVoiceProcessing, setIsVoiceProcessing] = useState<boolean>(false);
  const [voiceResult, setVoiceResult] = useState<VoiceTriageResponse | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  if (!isOpen) return null;

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

  const handleSelectPreset = (lang: "hi" | "as" | "en") => {
    setSelectedLanguage(lang);
    setInputText(samplePresets[lang].text);
  };

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
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#121826] border-l border-[#1E293B] w-full max-w-xl h-full flex flex-col shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E293B] bg-[#0B0F19]/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                Governed Multimodal AI Advisory Studio
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  INVARIANT 5
                </span>
              </h3>
              <p className="text-xs text-gray-400">
                Confidence-bounded AI suggestions with mandatory human commander authorization
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-[#1E293B] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Audio Waveform Simulator */}
          <div className="bg-[#0B0F19] border border-[#1E293B] rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <Mic className="w-4 h-4 text-purple-400" /> Multilingual Voice Emergency Dispatch
              </span>
              <span className="text-[10px] font-mono text-purple-400">WHISPER-V3 COMPATIBLE</span>
            </div>

            {/* Language Preset Tabs */}
            <div className="flex gap-2">
              {(["hi", "as", "en"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => handleSelectPreset(lang)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                    selectedLanguage === lang
                      ? "bg-purple-600 border-purple-500 text-white shadow-lg shadow-purple-600/30"
                      : "bg-[#121826] border-[#1E293B] text-gray-400 hover:text-white"
                  }`}
                >
                  {samplePresets[lang].label}
                </button>
              ))}
            </div>

            {/* Audio Wave Graphic */}
            <div className="bg-[#121826] border border-[#1E293B] rounded-xl p-3 flex items-center gap-3">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all ${
                  isPlayingAudio ? "bg-purple-600 text-white animate-pulse" : "bg-purple-500/20 text-purple-400"
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
                        isPlayingAudio ? "bg-purple-400 animate-pulse" : "bg-purple-500/30"
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
              className="w-full bg-[#121826] border border-[#1E293B] rounded-xl p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all font-mono"
            />

            {/* Action Button */}
            <button
              onClick={handleRunVoiceTriage}
              disabled={isVoiceProcessing || !inputText.trim()}
              className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-600/30 disabled:opacity-50"
            >
              {isVoiceProcessing ? (
                <RotateCcw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>Transcribe & Extract Structured Triage</span>
            </button>
          </div>

          {/* Structured Output & Explainable Priority Display */}
          {voiceResult && (
            <div className="bg-[#0B0F19] border border-purple-500/30 rounded-2xl p-5 space-y-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Advisory Triage Result
                </span>
                <span className="text-[10px] font-mono text-gray-400">
                  Latency: {voiceResult.transcription_latency_ms} ms • Hash: {voiceResult.prompt_hash}
                </span>
              </div>

              {/* Extraction Metrics */}
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-[#121826] p-2.5 rounded-xl border border-[#1E293B]">
                  <span className="text-[10px] text-gray-400 uppercase block">Category</span>
                  <span className="text-xs font-bold text-white">{voiceResult.extraction.category}</span>
                </div>
                <div className="bg-[#121826] p-2.5 rounded-xl border border-[#1E293B]">
                  <span className="text-[10px] text-gray-400 uppercase block">Severity</span>
                  <span className="text-xs font-bold text-red-400">{voiceResult.extraction.severity}</span>
                </div>
                <div className="bg-[#121826] p-2.5 rounded-xl border border-[#1E293B]">
                  <span className="text-[10px] text-gray-400 uppercase block">People at Risk</span>
                  <span className="text-xs font-bold text-amber-400">{voiceResult.extraction.estimated_people}</span>
                </div>
              </div>

              {/* Explainable Priority Score */}
              <div className="bg-[#121826] p-3.5 rounded-xl border border-amber-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-gray-300">Explainable Multi-Factor Priority</span>
                  <span className="text-sm font-black text-amber-400">
                    {voiceResult.urgency_score} / 100
                  </span>
                </div>
                {voiceResult.urgency_breakdown.explanation && (
                  <p className="text-[11px] text-gray-400 italic">
                    "{voiceResult.urgency_breakdown.explanation}"
                  </p>
                )}
              </div>

              {/* Official SOP Recommendation */}
              <div className="bg-[#121826] p-3.5 rounded-xl border border-[#1E293B] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-300">
                    {voiceResult.recommended_sop.title}
                  </span>
                  <span className="text-[10px] font-mono text-gray-500">
                    {voiceResult.recommended_sop.sop_code}
                  </span>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-semibold">
                    Mandatory Checklist:
                  </span>
                  <ul className="space-y-1 text-[11px] text-gray-300">
                    {voiceResult.recommended_sop.mandatory_checklist.slice(0, 3).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
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
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-600/30"
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

