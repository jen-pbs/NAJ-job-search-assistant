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
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
        <p className="text-sm text-red-700 font-medium">Backend not reachable</p>
        <p className="text-xs text-red-500 mt-1">
          Make sure the FastAPI server is running: <code className="bg-red-100 px-1 rounded">uvicorn app.main:app --reload</code> from the backend directory.
        </p>
      </div>
    );
  }

  if (!health) return null;

  const missing: string[] = [];
  if (!health.search_configured) missing.push("Search Engine");
  if (!health.notion_configured) missing.push("Notion API");
  if (!health.openai_configured) missing.push("OpenAI API (optional)");

  if (missing.length === 0) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
      <p className="text-sm text-amber-700 font-medium">Setup incomplete</p>
      <p className="text-xs text-amber-600 mt-1">
        Missing: {missing.join(", ")}. Check the{" "}
        <a
          href="http://localhost:8000/api/search/setup-guide"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-amber-800"
        >
          setup guide
        </a>{" "}
        for instructions.
      </p>
    </div>
  );
}
