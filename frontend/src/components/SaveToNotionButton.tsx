"use client";

import { useState } from "react";
import { saveToNotion } from "@/lib/api";
import { getDbForPurpose, NotionPurpose } from "./NotionManager";

interface SaveToNotionButtonProps {
  purpose: NotionPurpose;
  fields: Record<string, string | number | boolean>;
  label?: string;
}

export default function SaveToNotionButton({
  purpose,
  fields,
  label = "Save",
}: SaveToNotionButtonProps) {
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [notionUrl, setNotionUrl] = useState<string | null>(null);

  const dbConfig = getDbForPurpose(purpose);
  if (!dbConfig) return null;

  const handleSave = async () => {
    setStatus("saving");
    try {
      const result = await saveToNotion(dbConfig.databaseId, fields);
      setNotionUrl(result.notion_page?.url || null);
      setStatus("saved");
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  if (status === "saved") {
    return (
      <a
        href={notionUrl || "#"}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
        </svg>
        Saved
      </a>
    );
  }

  return (
    <button
      onClick={handleSave}
      disabled={status === "saving"}
      className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors ${
        status === "error"
          ? "text-red-600 bg-red-50 border-red-200"
          : "text-slate-600 bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300"
      }`}
    >
      {status === "saving" ? (
        <>
          <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={4} />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Saving...
        </>
      ) : status === "error" ? (
        "Failed"
      ) : (
        <>
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}
