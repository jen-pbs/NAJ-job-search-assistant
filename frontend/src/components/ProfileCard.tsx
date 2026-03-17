"use client";

import { useState } from "react";
import { LinkedInProfile, saveContact } from "@/lib/api";

interface ProfileCardProps {
  profile: LinkedInProfile;
  index: number;
}

export default function ProfileCard({ profile, index }: ProfileCardProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [notionUrl, setNotionUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const result = await saveContact({
        name: profile.name,
        headline: profile.headline || undefined,
        location: profile.location || undefined,
        linkedin_url: profile.linkedin_url,
        relevance_score: profile.relevance_score || undefined,
        relevance_reason: profile.relevance_reason || undefined,
        status: "Discovered",
      });
      setSaved(true);
      setNotionUrl(result.notion_page.url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const scoreColor =
    profile.relevance_score !== null
      ? profile.relevance_score >= 70
        ? "text-green-600 bg-green-50 border-green-200"
        : profile.relevance_score >= 40
          ? "text-yellow-600 bg-yellow-50 border-yellow-200"
          : "text-gray-500 bg-gray-50 border-gray-200"
      : "";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-xs text-gray-400 font-mono">#{index + 1}</span>
            <h3 className="font-semibold text-gray-900 truncate">{profile.name}</h3>
            {profile.relevance_score !== null && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${scoreColor}`}>
                {profile.relevance_score}/100
              </span>
            )}
          </div>

          {profile.headline && (
            <p className="text-sm text-gray-600 mb-1">{profile.headline}</p>
          )}

          {profile.location && (
            <p className="text-xs text-gray-400 mb-2">{profile.location}</p>
          )}

          {profile.relevance_reason && (
            <p className="text-xs text-blue-600 bg-blue-50 rounded-lg p-2 mb-2">
              {profile.relevance_reason}
            </p>
          )}

          {profile.snippet && (
            <p className="text-xs text-gray-400 line-clamp-2">{profile.snippet}</p>
          )}
        </div>

        <div className="flex flex-col gap-2 flex-shrink-0">
          <a
            href={profile.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors text-center"
          >
            View Profile
          </a>

          {saved ? (
            <div className="text-center">
              <span className="text-xs text-green-600 font-medium">Saved</span>
              {notionUrl && (
                <a
                  href={notionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-gray-400 hover:text-gray-600 mt-0.5"
                >
                  Open in Notion
                </a>
              )}
            </div>
          ) : (
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Save to Notion"}
            </button>
          )}
        </div>
      </div>

      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
    </div>
  );
}
