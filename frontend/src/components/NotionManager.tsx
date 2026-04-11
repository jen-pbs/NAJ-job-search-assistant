"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  listNotionDatabases,
  getNotionSchema,
  NotionDatabase,
  NotionSchema,
} from "@/lib/api";

const NOTION_DATABASES_STORAGE = "naj_notion_databases";

export type NotionPurpose = "people" | "jobs" | "events";

export interface NotionDbConfig {
  purpose: NotionPurpose;
  label: string;
  databaseId: string;
  databaseTitle: string;
}

export interface NotionManagerProps {
  notionConfigured: boolean;
  onConfigChange: (configs: NotionDbConfig[]) => void;
}

function purposeLabel(p: NotionPurpose): string {
  return p === "people" ? "People / Contacts" : p === "jobs" ? "Jobs" : "Events";
}

function purposeIcon(p: NotionPurpose): string {
  return p === "people" ? "\u{1F464}" : p === "jobs" ? "\u{1F4BC}" : "\u{1F4C5}";
}

export function getNotionDbConfigs(): NotionDbConfig[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(NOTION_DATABASES_STORAGE);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function getDbForPurpose(purpose: NotionPurpose): NotionDbConfig | null {
  const configs = getNotionDbConfigs();
  return configs.find((c) => c.purpose === purpose) || null;
}

export default function NotionManager({ notionConfigured, onConfigChange }: NotionManagerProps) {
  const [open, setOpen] = useState(false);
  const [databases, setDatabases] = useState<NotionDatabase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [configs, setConfigs] = useState<NotionDbConfig[]>([]);
  const [schemaPreview, setSchemaPreview] = useState<{
    db: NotionDatabase;
    schema: NotionSchema;
  } | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setConfigs(getNotionDbConfigs());
  }, []);

  const loadDatabases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dbs = await listNotionDatabases();
      setDatabases(dbs);
      setLoaded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to connect");
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-load databases when panel is opened for the first time (if backend has key)
  useEffect(() => {
    if (open && !loaded && notionConfigured) {
      loadDatabases();
    }
  }, [open, loaded, notionConfigured, loadDatabases]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleAssign = (purpose: NotionPurpose, db: NotionDatabase) => {
    const newConfigs = configs.filter((c) => c.purpose !== purpose);
    newConfigs.push({
      purpose,
      label: purposeLabel(purpose),
      databaseId: db.id,
      databaseTitle: db.title,
    });
    setConfigs(newConfigs);
    localStorage.setItem(NOTION_DATABASES_STORAGE, JSON.stringify(newConfigs));
    onConfigChange(newConfigs);
  };

  const handleRemove = (purpose: NotionPurpose) => {
    const newConfigs = configs.filter((c) => c.purpose !== purpose);
    setConfigs(newConfigs);
    localStorage.setItem(NOTION_DATABASES_STORAGE, JSON.stringify(newConfigs));
    onConfigChange(newConfigs);
  };

  const handlePreviewSchema = async (db: NotionDatabase) => {
    setSchemaLoading(true);
    try {
      const schema = await getNotionSchema(db.id);
      setSchemaPreview({ db, schema });
    } catch {
      setSchemaPreview(null);
    } finally {
      setSchemaLoading(false);
    }
  };

  const configuredCount = configs.length;

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
          configuredCount > 0
            ? "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
            : notionConfigured
            ? "bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100"
            : "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100"
        }`}
      >
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
        Notion{configuredCount > 0 ? ` (${configuredCount})` : ""}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-[420px] bg-white border border-slate-200 rounded-xl shadow-xl p-4 z-50 max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-800">Notion Databases</h3>
            <button
              onClick={loadDatabases}
              disabled={loading}
              className="text-[10px] text-indigo-500 hover:text-indigo-700 font-medium"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {!notionConfigured && databases.length === 0 && (
            <div className="text-center py-4 mb-3 bg-amber-50 rounded-lg border border-amber-100">
              <p className="text-xs text-amber-600 mb-1 font-medium">Notion API key not configured</p>
              <p className="text-[10px] text-amber-500">
                Add <code className="bg-amber-100 px-1 rounded">NOTION_API_KEY</code> to your <code className="bg-amber-100 px-1 rounded">.env</code> file and restart the backend.
              </p>
              <p className="text-[10px] text-amber-400 mt-1">
                Create at{" "}
                <a href="https://www.notion.so/my-integrations" target="_blank" rel="noopener noreferrer" className="text-indigo-500 underline">
                  notion.so/my-integrations
                </a>
              </p>
            </div>
          )}

          {error && <p className="text-xs text-red-500 mb-3">{error}</p>}

          {/* Assigned databases */}
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-600 mb-2">Assigned Databases</p>
            {(["people", "jobs", "events"] as NotionPurpose[]).map((purpose) => {
              const cfg = configs.find((c) => c.purpose === purpose);
              return (
                <div key={purpose} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-slate-50 mb-1">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm">{purposeIcon(purpose)}</span>
                    <span className="text-xs font-medium text-slate-700">{purposeLabel(purpose)}</span>
                    {cfg ? (
                      <span className="text-xs text-slate-400 truncate max-w-[150px]" title={cfg.databaseTitle}>
                        &rarr; {cfg.databaseTitle}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-300 italic">not set</span>
                    )}
                  </div>
                  {cfg && (
                    <button
                      onClick={() => handleRemove(purpose)}
                      className="text-xs text-red-400 hover:text-red-600 px-1"
                      title="Unlink"
                    >
                      ✕
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Available databases */}
          {databases.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-600 mb-2">
                Available Databases ({databases.length})
              </p>
              <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
                {databases.map((db) => (
                  <div key={db.id} className="border border-slate-100 rounded-lg p-2.5">
                    <div className="flex items-center justify-between mb-1.5">
                      <button
                        onClick={() => handlePreviewSchema(db)}
                        className="text-xs font-medium text-slate-800 hover:text-indigo-600 text-left truncate max-w-[200px]"
                        title={db.title || "Untitled"}
                      >
                        {db.title || "Untitled"}
                      </button>
                      <div className="flex gap-1">
                        {(["people", "jobs", "events"] as NotionPurpose[]).map((p) => (
                          <button
                            key={p}
                            onClick={() => handleAssign(p, db)}
                            className={`text-[10px] px-1.5 py-0.5 rounded border transition-all ${
                              configs.find((c) => c.purpose === p && c.databaseId === db.id)
                                ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                                : "text-slate-400 border-slate-200 hover:border-indigo-200 hover:text-indigo-500"
                            }`}
                            title={`Use for ${purposeLabel(p)}`}
                          >
                            {purposeIcon(p)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(db.columns).slice(0, 6).map(([name, type]) => (
                        <span key={name} className="text-[9px] px-1.5 py-0.5 bg-slate-50 text-slate-400 rounded">
                          {name} <span className="text-slate-300">({type})</span>
                        </span>
                      ))}
                      {Object.keys(db.columns).length > 6 && (
                        <span className="text-[9px] px-1.5 py-0.5 text-slate-300">
                          +{Object.keys(db.columns).length - 6} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-4">
              <p className="text-xs text-slate-400">Loading databases...</p>
            </div>
          )}

          {/* Schema preview */}
          {schemaLoading && (
            <p className="text-xs text-slate-400 mt-3">Loading schema...</p>
          )}
          {schemaPreview && !schemaLoading && (
            <div className="mt-3 border border-slate-100 rounded-lg p-3 bg-slate-50">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-700">
                  {schemaPreview.db.title} — Schema
                </p>
                <button onClick={() => setSchemaPreview(null)} className="text-xs text-slate-400 hover:text-slate-600">✕</button>
              </div>
              <div className="space-y-1">
                {Object.entries(schemaPreview.schema.properties).map(([name, prop]) => (
                  <div key={name} className="flex items-center gap-2 text-[10px]">
                    <span className="font-medium text-slate-600 min-w-[80px]">{name}</span>
                    <span className="text-slate-400">{prop.type}</span>
                    {prop.options && prop.options.length > 0 && (
                      <span className="text-slate-300 truncate max-w-[150px]">
                        [{prop.options.slice(0, 4).join(", ")}{prop.options.length > 4 ? "..." : ""}]
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
