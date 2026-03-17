"use client";

import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ProfileCard from "@/components/ProfileCard";
import StatusBanner from "@/components/StatusBanner";
import NetworkBackground from "@/components/NetworkBackground";
import { findPeople, LinkedInProfile } from "@/lib/api";

export default function Home() {
  const [profiles, setProfiles] = useState<LinkedInProfile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryUsed, setQueryUsed] = useState<string | null>(null);
  const [totalFound, setTotalFound] = useState(0);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setProfiles([]);
    setQueryUsed(null);

    try {
      const result = await findPeople({ query, max_results: 20 });
      setProfiles(result.profiles);
      setQueryUsed(result.query_used);
      setTotalFound(result.total_found);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 relative">
      <NetworkBackground />

      {/* Header */}
      <header className="border-b border-slate-200/60 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">N</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900 tracking-tight">
                NAJ <span className="text-indigo-600">Search</span>
              </h1>
              <p className="text-[10px] text-slate-400 -mt-0.5 tracking-wide uppercase">
                Network &amp; Job Assistant
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBanner />
          </div>
        </div>
      </header>

      {/* Hero + Search */}
      <div className="max-w-5xl mx-auto px-6 pt-12 pb-6 relative z-[1]">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-slate-800 mb-2">
            Find the right people to talk to
          </h2>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">
            Describe who you&apos;re looking for. NAJ searches LinkedIn profiles, scores relevance with AI, and explains why each person is a good match.
          </p>
        </div>

        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      </div>

      {/* Results */}
      <div className="max-w-5xl mx-auto px-6 pb-20 relative z-[1]">
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200/60 rounded-xl p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {queryUsed && (
          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
              <p className="text-sm text-slate-600">
                <span className="font-semibold text-slate-800">{totalFound}</span> profiles found
              </p>
            </div>
            <p className="text-xs text-slate-400 max-w-sm truncate font-mono" title={queryUsed}>
              {queryUsed}
            </p>
          </div>
        )}

        {profiles.length > 0 && (
          <div className="mt-4 space-y-3">
            {profiles.map((profile, i) => (
              <ProfileCard key={profile.linkedin_url} profile={profile} index={i} />
            ))}
          </div>
        )}

        {isLoading && (
          <div className="mt-16 flex flex-col items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-2 border-indigo-100 border-t-indigo-500 animate-spin"></div>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-slate-600">Searching LinkedIn profiles...</p>
              <p className="text-xs text-slate-400 mt-1">This may take 10-15 seconds</p>
            </div>
          </div>
        )}

        {!isLoading && profiles.length === 0 && !error && !queryUsed && (
          <div className="mt-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
              </svg>
            </div>
            <p className="text-slate-400 text-sm">
              Describe who you want to connect with above
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
