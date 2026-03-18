"use client";

import { useState, useEffect, useCallback } from "react";
import SearchBar from "@/components/SearchBar";
import ProfileCard from "@/components/ProfileCard";
import EventCard from "@/components/EventCard";
import ChatPanel from "@/components/ChatPanel";
import StatusBanner from "@/components/StatusBanner";
import NetworkBackground from "@/components/NetworkBackground";
import {
  findPeople,
  searchEvents,
  LinkedInProfile,
  Event,
} from "@/lib/api";

const LOADING_MESSAGES = [
  "Searching across DuckDuckGo, Brave, Bing, and Google...",
  "Sneaking into public LinkedIn pages (legally, I promise)...",
  "Checking Google Scholar for publications...",
  "Looking up ORCID career timelines...",
  "Scanning press releases and conference bios...",
  "AI is reading through all the profiles...",
  "Scoring relevance for each person...",
  "This is the part where you grab a coffee...",
  "Juggling 6 data sources at once... don't drop any...",
  "Consulting the crystal ball of career networking...",
  "Running faster than a recruiter sliding into DMs...",
  "Cross-referencing data like a detective with a spreadsheet...",
  "Pretending to be a regular browser... nothing to see here...",
  "Visiting more websites than you do on a lazy Sunday...",
  "Reading academic papers so you don't have to...",
  "Rolling for initiative... nat 20! Extra profiles found!",
  "Fetching data... good bot, good bot...",
  "Piecing together professional histories like a puzzle...",
  "Almost there... just polishing the results...",
];

function SearchLoadingAnimation({ query }: { query?: string }) {
  const [msgIndex, setMsgIndex] = useState(0);
  const [tailWag, setTailWag] = useState(false);

  useEffect(() => {
    setMsgIndex(Math.floor(Math.random() * LOADING_MESSAGES.length));
  }, []);

  useEffect(() => {
    const msgTimer = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 6000);
    return () => clearInterval(msgTimer);
  }, []);

  useEffect(() => {
    const wagTimer = setInterval(() => {
      setTailWag((prev) => !prev);
    }, 400);
    return () => clearInterval(wagTimer);
  }, []);

  // Extract field from search query for targeted messages
  const fieldHint = query?.toLowerCase() || "";
  let fieldMessage = "Searching for the best connections in your field...";
  if (fieldHint.includes("heor") || fieldHint.includes("health econom"))
    fieldMessage = "Deep-diving into health economics and outcomes research networks...";
  else if (fieldHint.includes("pharma") || fieldHint.includes("biotech"))
    fieldMessage = "Scanning pharma and biotech professional networks...";
  else if (fieldHint.includes("data science") || fieldHint.includes("machine learning"))
    fieldMessage = "Crunching through data science and ML communities...";
  else if (fieldHint.includes("medical") || fieldHint.includes("clinical"))
    fieldMessage = "Searching medical and clinical research circles...";
  else if (fieldHint.includes("market access") || fieldHint.includes("pricing"))
    fieldMessage = "Exploring market access and pricing strategy networks...";
  else if (fieldHint.includes("epidemiol"))
    fieldMessage = "Investigating epidemiology and public health networks...";
  else if (fieldHint.includes("regulat") || fieldHint.includes("fda"))
    fieldMessage = "Navigating regulatory affairs professional networks...";
  else if (fieldHint.includes("finance") || fieldHint.includes("invest"))
    fieldMessage = "Scanning finance and investment professional circles...";
  else if (fieldHint.includes("engineer") || fieldHint.includes("software"))
    fieldMessage = "Searching software engineering and tech communities...";
  else if (fieldHint.includes("consult"))
    fieldMessage = "Browsing consulting networks and advisory circles...";

  const messages = [fieldMessage, ...LOADING_MESSAGES];
  const msg = messages[msgIndex % messages.length];

  return (
    <div className="mt-16 flex flex-col items-center gap-5">
      {/* Animated dog character - SVG */}
      <div className="relative">
        <svg width="80" height="80" viewBox="0 0 100 100" className="animate-bounce" style={{ animationDuration: "2s" }}>
          {/* Body */}
          <ellipse cx="50" cy="62" rx="22" ry="18" fill="none" stroke="black" strokeWidth="2.5" />
          {/* Head */}
          <circle cx="50" cy="35" r="16" fill="none" stroke="black" strokeWidth="2.5" />
          {/* Left ear (floppy) */}
          <path d="M36 28 Q28 15 24 28" fill="none" stroke="black" strokeWidth="2.5" strokeLinecap="round" />
          {/* Right ear (floppy) */}
          <path d="M64 28 Q72 15 76 28" fill="none" stroke="black" strokeWidth="2.5" strokeLinecap="round" />
          {/* Eyes */}
          <circle cx="44" cy="33" r="2.5" fill="black" />
          <circle cx="56" cy="33" r="2.5" fill="black" />
          {/* Eye sparkle */}
          <circle cx="45" cy="32" r="0.8" fill="white" />
          <circle cx="57" cy="32" r="0.8" fill="white" />
          {/* Nose */}
          <ellipse cx="50" cy="39" rx="3" ry="2" fill="black" />
          {/* Mouth - happy */}
          <path d="M45 42 Q50 47 55 42" fill="none" stroke="black" strokeWidth="1.5" strokeLinecap="round" />
          {/* Tongue */}
          <path d="M50 44 Q51 48 50 49" fill="none" stroke="black" strokeWidth="1.5" strokeLinecap="round" />
          {/* Front legs */}
          <line x1="38" y1="76" x2="36" y2="88" stroke="black" strokeWidth="2.5" strokeLinecap="round" />
          <line x1="62" y1="76" x2="64" y2="88" stroke="black" strokeWidth="2.5" strokeLinecap="round" />
          {/* Paws */}
          <circle cx="35" cy="89" r="2.5" fill="none" stroke="black" strokeWidth="2" />
          <circle cx="65" cy="89" r="2.5" fill="none" stroke="black" strokeWidth="2" />
          {/* Tail - wagging */}
          <path
            d={tailWag ? "M72 55 Q85 42 88 50" : "M72 55 Q85 48 82 56"}
            fill="none" stroke="black" strokeWidth="2.5" strokeLinecap="round"
            style={{ transition: "d 0.3s ease-in-out" }}
          />
          {/* Collar */}
          <path d="M38 48 Q50 52 62 48" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" />
          {/* Collar tag */}
          <circle cx="50" cy="52" r="3" fill="none" stroke="black" strokeWidth="1.5" />
          <text x="50" y="54" textAnchor="middle" fontSize="4" fontWeight="bold" fill="black">N</text>
        </svg>
        {/* Shadow */}
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-12 h-2 bg-slate-200/60 rounded-full animate-pulse" />
      </div>

      {/* Message bubble */}
      <div className="bg-white border border-slate-200 rounded-2xl px-6 py-3.5 shadow-sm max-w-md relative">
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white border-l border-t border-slate-200 rotate-45" />
        <p className="text-sm text-slate-600 text-center relative z-10 leading-relaxed">
          {msg}
        </p>
      </div>

      <p className="text-xs text-slate-400">
        Searching 6 sources in parallel
      </p>
    </div>
  );
}

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
  const [chatProfile, setChatProfile] = useState<LinkedInProfile | null>(null);
  const [lastSearchInput, setLastSearchInput] = useState("");

  // Events state
  const [events, setEvents] = useState<Event[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [eventsQuery, setEventsQuery] = useState<string | null>(null);
  const [freeOnly, setFreeOnly] = useState(false);

  // User name
  const [userName, setUserName] = useState<string | null>(null);
  const [nameInput, setNameInput] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("naj_user_name");
    if (saved) setUserName(saved);
  }, []);

  const handleSetName = () => {
    if (nameInput.trim()) {
      const name = nameInput.trim();
      setUserName(name);
      localStorage.setItem("naj_user_name", name);
    }
  };

  const filteredEvents = freeOnly ? events.filter((e) => e.is_free === true) : events;

  const handlePeopleSearch = async (query: string) => {
    setLastSearchInput(query);
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
      subtitle: "Find conferences, meetups, career fairs, and networking events. NAJ searches Eventbrite, Meetup, ISPOR, ASHEcon, Biocom, BIO, and more.",
      placeholder: "Search for events, conferences, career fairs...",
      examples: [
        "HEOR conferences 2026",
        "Pharma biotech career fair California",
        "ISPOR annual meeting",
        "Biotech networking meetups San Francisco",
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

  // Welcome screen
  if (!userName) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 relative flex items-center justify-center">
        <NetworkBackground />
        <div className="relative z-[1] max-w-md w-full mx-4">
          <div className="bg-white/90 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-8 shadow-lg text-center">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-5 shadow-md">
              <span className="text-white font-bold text-xl">N</span>
            </div>
            <h1 className="text-2xl font-semibold text-slate-800 mb-1">
              Welcome to <span className="text-indigo-600">NAJ Search</span>
            </h1>
            <p className="text-sm text-slate-400 mb-6">
              Your Network and Job Search Assistant
            </p>
            <p className="text-sm text-slate-600 mb-4">What&apos;s your name?</p>
            <form
              onSubmit={(e) => { e.preventDefault(); handleSetName(); }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                placeholder="Enter your first name..."
                className="flex-1 px-4 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 bg-white text-slate-800 placeholder-slate-400"
                autoFocus
              />
              <button
                type="submit"
                disabled={!nameInput.trim()}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-xl hover:from-indigo-700 hover:to-indigo-600 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 text-sm font-medium transition-all"
              >
                Start
              </button>
            </form>
          </div>
        </div>
      </main>
    );
  }

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
          <p className="text-3xl text-indigo-500 font-bold mb-2">
            Hi, {userName}
          </p>
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
                  <ProfileCard key={profile.linkedin_url} profile={profile} index={i} onChat={setChatProfile} />
                ))}
              </div>
            )}

            {peopleLoading && <SearchLoadingAnimation query={lastSearchInput} />}

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
                    <span className="font-semibold text-slate-800">{filteredEvents.length}</span> events found
                    {freeOnly && events.length !== filteredEvents.length && (
                      <span className="text-slate-400"> ({events.length} total)</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => setFreeOnly(!freeOnly)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                    freeOnly
                      ? "bg-green-50 text-green-700 border-green-200"
                      : "bg-white text-slate-500 border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span>{freeOnly ? "Showing free only" : "Show free only"}</span>
                </button>
              </div>
            )}

            {filteredEvents.length > 0 && (
              <div className="mt-4 space-y-3">
                {filteredEvents.map((event, i) => (
                  <EventCard key={event.url + i} event={event} index={i} />
                ))}
              </div>
            )}

            {eventsLoading && <SearchLoadingAnimation />}

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

      {chatProfile && (
        <ChatPanel profile={chatProfile} onClose={() => setChatProfile(null)} />
      )}
    </main>
  );
}
