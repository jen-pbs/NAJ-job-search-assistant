"use client";

import { useEffect, useState, useRef } from "react";
import { checkHealth, HealthStatus } from "@/lib/api";

const DEFAULT_AI_MODEL = "llama-3.3-70b-versatile";
const DEFAULT_AI_PROVIDER = "groq";
const USER_AI_MODEL_STORAGE_KEY = "naj_ai_model";
const USER_AI_PROVIDER_STORAGE_KEY = "naj_ai_provider";
const USER_AI_BASE_URL_STORAGE_KEY = "naj_ai_base_url";
const USER_AI_API_KEY_SESSION_KEY = "naj_ai_api_key";

const DEFAULT_PROVIDER_BASE_URLS: Record<string, string> = {
  groq: "https://api.groq.com/openai/v1",
  openai: "https://api.openai.com/v1",
  openrouter: "https://openrouter.ai/api/v1",
};

export interface AiSettings {
  aiModel: string;
  aiProvider: string;
  aiBaseUrl: string;
  aiApiKey: string;
}

interface StatusBannerProps {
  aiSettings: AiSettings;
  onAiSettingsChange: (settings: AiSettings) => void;
}

export default function StatusBanner({ aiSettings, onAiSettingsChange }: StatusBannerProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState(false);
  const [showModelUpdate, setShowModelUpdate] = useState(false);
  const [modelInput, setModelInput] = useState(aiSettings.aiModel || DEFAULT_AI_MODEL);
  const [providerInput, setProviderInput] = useState(aiSettings.aiProvider || DEFAULT_AI_PROVIDER);
  const [baseUrlInput, setBaseUrlInput] = useState(aiSettings.aiBaseUrl || "");
  const [apiKeyInput, setApiKeyInput] = useState(aiSettings.aiApiKey || "");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowModelUpdate(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleUpdateModel = () => {
    const provider = providerInput.trim().toLowerCase() || DEFAULT_AI_PROVIDER;
    const model = modelInput.trim() || DEFAULT_AI_MODEL;
    const defaultBase = DEFAULT_PROVIDER_BASE_URLS[provider] || "";
    const baseUrl = baseUrlInput.trim() || defaultBase;
    const apiKey = apiKeyInput.trim();

    localStorage.setItem(USER_AI_MODEL_STORAGE_KEY, model);
    localStorage.setItem(USER_AI_PROVIDER_STORAGE_KEY, provider);
    if (baseUrl) localStorage.setItem(USER_AI_BASE_URL_STORAGE_KEY, baseUrl);
    else localStorage.removeItem(USER_AI_BASE_URL_STORAGE_KEY);

    if (apiKey) sessionStorage.setItem(USER_AI_API_KEY_SESSION_KEY, apiKey);
    else sessionStorage.removeItem(USER_AI_API_KEY_SESSION_KEY);

    onAiSettingsChange({
      aiModel: model,
      aiProvider: provider,
      aiBaseUrl: baseUrl,
      aiApiKey: apiKey,
    });
    setShowModelUpdate(false);
  };

  return (
    <div className="relative flex items-center gap-2" ref={dropdownRef}>
      {error ? (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200/60 rounded-lg">
          <div className="w-2 h-2 rounded-full bg-red-400"></div>
          <span className="text-xs text-red-600 font-medium">Backend offline</span>
        </div>
      ) : health && (!health.ai_configured) ? (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200/60 rounded-lg">
          <div className="w-2 h-2 rounded-full bg-amber-400"></div>
          <span className="text-xs text-amber-600">
            Missing: AI scoring
          </span>
        </div>
      ) : null}

      <button
        onClick={() => {
          if (!showModelUpdate) {
            setModelInput(aiSettings.aiModel || DEFAULT_AI_MODEL);
            setProviderInput(aiSettings.aiProvider || DEFAULT_AI_PROVIDER);
            setBaseUrlInput(aiSettings.aiBaseUrl || "");
            setApiKeyInput(aiSettings.aiApiKey || "");
          }
          setShowModelUpdate((prev) => !prev);
        }}
        className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200/60 rounded-lg hover:bg-indigo-100 transition-colors"
      >
        Update model
      </button>

      {showModelUpdate && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg p-3 z-50">
          <p className="text-xs text-slate-500 mb-2">Update AI provider + key</p>
          <div className="space-y-2">
            <input
              type="text"
              value={providerInput}
              onChange={(e) => setProviderInput(e.target.value)}
              placeholder="Provider (e.g. groq, openai, openrouter)"
              className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-300"
            />
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="API key (session only)"
              className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-300"
            />
            <input
              type="text"
              value={baseUrlInput}
              onChange={(e) => setBaseUrlInput(e.target.value)}
              placeholder="Base URL (optional for known providers)"
              className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-300"
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2 mb-1">Model</p>
          <input
            type="text"
            value={modelInput}
            onChange={(e) => setModelInput(e.target.value)}
            placeholder={DEFAULT_AI_MODEL}
            className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-300"
          />
          <div className="mt-2 flex justify-end gap-2">
            <button
              onClick={() => setShowModelUpdate(false)}
              className="px-2.5 py-1.5 text-xs text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateModel}
              className="px-2.5 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100"
            >
              Save settings
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
