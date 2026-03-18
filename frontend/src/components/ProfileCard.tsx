"use client";

import { useState } from "react";
import { LinkedInProfile, saveContact } from "@/lib/api";

interface ProfileCardProps {
  profile: LinkedInProfile;
  index: number;
  onChat?: (profile: LinkedInProfile) => void;
}

export default function ProfileCard({ profile, index, onChat }: ProfileCardProps) {
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
        company: profile.company || undefined,
        role_title: profile.role_title || undefined,
        field: profile.field || undefined,
        company_type: profile.company_type || undefined,
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

  const getScoreBadge = () => {
    if (profile.relevance_score === null || profile.relevance_score === undefined) return null;
    const score = profile.relevance_score;

    let colorClasses: string;
    let label: string;
    if (score >= 75) {
      colorClasses = "bg-emerald-50 text-emerald-700 border-emerald-200";
      label = "Strong match";
    } else if (score >= 50) {
      colorClasses = "bg-amber-50 text-amber-700 border-amber-200";
      label = "Possible match";
    } else {
      colorClasses = "bg-slate-50 text-slate-500 border-slate-200";
      label = "Weak match";
    }

    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${colorClasses}`}>
        <span>{score}</span>
        <span className="text-[10px] font-normal opacity-70">{label}</span>
      </div>
    );
  };

  return (
    <div className="bg-white border border-slate-200/60 rounded-xl p-5 hover:border-slate-300 hover:shadow-sm transition-all group">
      <div className="flex items-start gap-4">
        {/* Avatar placeholder */}
        <div className="w-11 h-11 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center flex-shrink-0">
          <span className="text-indigo-600 font-semibold text-sm">
            {profile.name.split(" ").map(n => n[0]).slice(0, 2).join("")}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] text-slate-300 font-mono">#{index + 1}</span>
                <h3 className="font-semibold text-slate-900 truncate">{profile.name}</h3>
                {getScoreBadge()}
              </div>

              {profile.headline && (
                <p className="text-sm text-slate-600 leading-snug">{profile.headline}</p>
              )}

              {profile.location && (
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                  </svg>
                  {profile.location}
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {onChat && (
                <button
                  onClick={() => onChat(profile)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-600 border border-purple-200/60 rounded-lg hover:bg-purple-50 transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
                  </svg>
                  Chat
                </button>
              )}
              <a
                href={profile.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 border border-indigo-200/60 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                Profile
              </a>

              {saved ? (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 border border-emerald-200/60 rounded-lg">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  {notionUrl ? (
                    <a href={notionUrl} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      Saved
                    </a>
                  ) : "Saved"}
                </div>
              ) : (
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200/60 rounded-lg hover:bg-slate-50 hover:border-slate-300 disabled:opacity-50 transition-colors"
                >
                  {saving ? (
                    <>
                      <div className="w-3 h-3 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin"></div>
                      Saving
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
                      </svg>
                      Save to Notion
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* AI Reasoning */}
          {profile.relevance_reason && (
            <div className="mt-3 flex gap-2 items-start">
              <div className="w-5 h-5 rounded-md bg-indigo-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3 h-3 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
                </svg>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                {profile.relevance_reason}
              </p>
            </div>
          )}

          {/* Snippet fallback */}
          {!profile.relevance_reason && profile.snippet && (
            <p className="mt-2 text-xs text-slate-400 line-clamp-2 leading-relaxed">{profile.snippet}</p>
          )}
        </div>
      </div>

      {error && <p className="text-xs text-red-500 mt-3 ml-15">{error}</p>}
    </div>
  );
}
