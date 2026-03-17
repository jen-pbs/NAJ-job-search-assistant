"use client";

import { useEffect, useState } from "react";
import { checkHealth, HealthStatus } from "@/lib/api";

export default function StatusBanner() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200/60 rounded-lg">
        <div className="w-2 h-2 rounded-full bg-red-400"></div>
        <span className="text-xs text-red-600 font-medium">Backend offline</span>
      </div>
    );
  }

  if (!health) return null;

  const allGood = health.search_configured && health.notion_configured;

  if (allGood && health.ai_configured) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200/60 rounded-lg">
        <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
        <span className="text-xs text-emerald-600 font-medium">All systems ready</span>
      </div>
    );
  }

  const missing: string[] = [];
  if (!health.notion_configured) missing.push("Notion");
  if (!health.ai_configured) missing.push("AI scoring");

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200/60 rounded-lg">
      <div className="w-2 h-2 rounded-full bg-amber-400"></div>
      <span className="text-xs text-amber-600">
        Missing: {missing.join(", ")}
      </span>
    </div>
  );
}
