"use client";

import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ProfileCard from "@/components/ProfileCard";
import StatusBanner from "@/components/StatusBanner";
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
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Job Search Assistant
          </h1>
          <p className="text-gray-500 text-sm">
            Find people for informational interviews. Describe who you are looking for and let AI do the rest.
          </p>
        </div>

        <StatusBanner />

        <SearchBar onSearch={handleSearch} isLoading={isLoading} />

        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4 max-w-3xl mx-auto">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {queryUsed && (
          <div className="mt-8 max-w-3xl mx-auto">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-500">
                Found <span className="font-medium text-gray-700">{totalFound}</span> profiles
              </p>
              <p className="text-xs text-gray-400 max-w-md truncate" title={queryUsed}>
                Query: {queryUsed}
              </p>
            </div>
          </div>
        )}

        {profiles.length > 0 && (
          <div className="mt-4 max-w-3xl mx-auto space-y-3">
            {profiles.map((profile, i) => (
              <ProfileCard key={profile.linkedin_url} profile={profile} index={i} />
            ))}
          </div>
        )}

        {isLoading && (
          <div className="mt-12 text-center">
            <div className="inline-flex items-center gap-3 text-gray-500">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm">Searching LinkedIn profiles via Google...</span>
            </div>
          </div>
        )}

        {!isLoading && profiles.length === 0 && !error && !queryUsed && (
          <div className="mt-16 text-center text-gray-400 text-sm">
            <p>Enter a search query above to find people for informational interviews.</p>
          </div>
        )}
      </div>
    </main>
  );
}
