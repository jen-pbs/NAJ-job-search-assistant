"use client";

import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ProfileCard from "@/components/ProfileCard";
import EventCard from "@/components/EventCard";
import StatusBanner from "@/components/StatusBanner";
import NetworkBackground from "@/components/NetworkBackground";
import {
  findPeople,
  searchEvents,
  LinkedInProfile,
  Event,
} from "@/lib/api";

type Tab = "networking" | "events" | "jobs";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  {
    id: "networking",
    label: "People",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
      </svg>
    ),
  },
  {
    id: "events",
    label: "Events",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
      </svg>
    ),
  },
  {
    id: "jobs",
    label: "Jobs",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0M12 12.75h.008v.008H12v-.008Z" />
      </svg>
    ),
  },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("networking");

  // People state
  const [profiles, setProfiles] = useState<LinkedInProfile[]>([]);
  const [peopleLoading, setPeopleLoading] = useState(false);
  const [peopleError, setPeopleError] = useState<string | null>(null);
  const [peopleQuery, setPeopleQuery] = useState<string | null>(null);

  // Events state
  const [events, setEvents] = useState<Event[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [eventsQuery, setEventsQuery] = useState<string | null>(null);

  const handlePeopleSearch = async (query: string) => {
    setPeopleLoading(true);
    setPeopleError(null);
    setProfiles([]);
    setPeopleQuery(null);
    try {
      const result = await findPeople({ query, max_results: 20 });
      setProfiles(result.profiles);
      setPeopleQuery(result.query_used);
    } catch (e) {
      setPeopleError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setPeopleLoading(false);
    }
  };

  const handleEventSearch = async (query: string) => {
    setEventsLoading(true);
    setEventsError(null);
    setEvents([]);
    setEventsQuery(null);
    try {
      const result = await searchEvents({ query, max_results: 15 });
      setEvents(result.events);
      setEventsQuery(result.query_used);
    } catch (e) {
      setEventsError(e instanceof Error ? e.message : "Event search failed");
    } finally {
      setEventsLoading(false);
    }
  };

  const tabConfig = {
    networking: {
      title: "Find the right people to talk to",
      subtitle: "Describe who you're looking for. NAJ searches LinkedIn profiles, scores relevance with AI, and explains why each person is a good match.",
      placeholder: "Describe the people you want to connect with...",
      examples: [
        "HEOR researchers at large pharma companies",
        "Health economics analysts with consulting experience",
        "Directors of outcomes research at Pfizer or Roche",
        "People who transitioned from academia to HEOR",
      ],
    },
    events: {
      title: "Discover networking events",
      subtitle: "Find conferences, meetups, and networking events in your field. NAJ searches across Eventbrite, Meetup, and professional associations.",
      placeholder: "Search for events, conferences, meetups...",
      examples: [
        "HEOR conferences 2026",
        "Health economics networking events",
        "ISPOR annual meeting",
        "Pharma industry meetups Bay Area",
      ],
    },
    jobs: {
      title: "Job search",
      subtitle: "Search for job opportunities in your field. Coming soon -- this feature is under development.",
      placeholder: "Search for job postings...",
      examples: [
        "HEOR analyst positions",
        "Health economics manager jobs",
        "Real-world evidence scientist roles",
      ],
    },
  };

  const current = tabConfig[activeTab];
  const isLoading = activeTab === "networking" ? peopleLoading : activeTab === "events" ? eventsLoading : false;

  const handleSearch = (query: string) => {
    if (activeTab === "networking") handlePeopleSearch(query);
    else if (activeTab === "events") handleEventSearch(query);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 relative">
      <NetworkBackground />

      {/* Header */}
      <header className="border-b border-slate-200/60 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between mb-3">
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
            <StatusBanner />
          </div>

          {/* Tab navigation */}
          <nav className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  activeTab === tab.id
                    ? "bg-indigo-50 text-indigo-700 shadow-sm"
                    : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 pt-10 pb-6 relative z-[1]">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-slate-800 mb-2">
            {current.title}
          </h2>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">
            {current.subtitle}
          </p>
        </div>

        {activeTab !== "jobs" ? (
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder={current.placeholder}
            examples={current.examples}
          />
        ) : (
          <div className="max-w-3xl mx-auto">
            <div className="bg-white border border-slate-200/60 rounded-2xl p-8 text-center">
              <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437 1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008Z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-700 mb-2">Coming Soon</h3>
              <p className="text-sm text-slate-400">
                Job search aggregation is being built. For now, focus on networking -- that&apos;s where the best opportunities come from.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="max-w-5xl mx-auto px-6 pb-20 relative z-[1]">
        {/* People results */}
        {activeTab === "networking" && (
          <>
            {peopleError && (
              <div className="mt-4 bg-red-50 border border-red-200/60 rounded-xl p-4">
                <p className="text-sm text-red-600">{peopleError}</p>
              </div>
            )}

            {peopleQuery && (
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                  <p className="text-sm text-slate-600">
                    <span className="font-semibold text-slate-800">{profiles.length}</span> profiles found
                  </p>
                </div>
                <p className="text-xs text-slate-400 max-w-sm truncate font-mono" title={peopleQuery}>
                  {peopleQuery}
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

            {peopleLoading && (
              <div className="mt-16 flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full border-2 border-indigo-100 border-t-indigo-500 animate-spin"></div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-600">Searching &amp; evaluating profiles...</p>
                  <p className="text-xs text-slate-400 mt-1">AI is analyzing each profile. This may take 30-60 seconds.</p>
                </div>
              </div>
            )}

            {!peopleLoading && profiles.length === 0 && !peopleError && !peopleQuery && (
              <div className="mt-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
                  </svg>
                </div>
                <p className="text-slate-400 text-sm">Describe who you want to connect with above</p>
              </div>
            )}
          </>
        )}

        {/* Events results */}
        {activeTab === "events" && (
          <>
            {eventsError && (
              <div className="mt-4 bg-red-50 border border-red-200/60 rounded-xl p-4">
                <p className="text-sm text-red-600">{eventsError}</p>
              </div>
            )}

            {eventsQuery && (
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                  <p className="text-sm text-slate-600">
                    <span className="font-semibold text-slate-800">{events.length}</span> events found
                  </p>
                </div>
              </div>
            )}

            {events.length > 0 && (
              <div className="mt-4 space-y-3">
                {events.map((event, i) => (
                  <EventCard key={event.url + i} event={event} index={i} />
                ))}
              </div>
            )}

            {eventsLoading && (
              <div className="mt-16 flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full border-2 border-indigo-100 border-t-indigo-500 animate-spin"></div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-600">Searching for events...</p>
                  <p className="text-xs text-slate-400 mt-1">Checking Eventbrite, Meetup, and professional associations</p>
                </div>
              </div>
            )}

            {!eventsLoading && events.length === 0 && !eventsError && !eventsQuery && (
              <div className="mt-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
                  </svg>
                </div>
                <p className="text-slate-400 text-sm">Search for conferences, meetups, and networking events</p>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
