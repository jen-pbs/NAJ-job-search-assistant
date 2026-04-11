"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";

const DotLottieReact = dynamic(
  () => import("@lottiefiles/dotlottie-react").then((m) => m.DotLottieReact),
  { ssr: false },
);
import SearchBar from "@/components/SearchBar";
import ProfileCard from "@/components/ProfileCard";
import EventCard from "@/components/EventCard";
import JobCard from "@/components/JobCard";
import ChatPanel from "@/components/ChatPanel";
import StatusBanner from "@/components/StatusBanner";
import NotionManager from "@/components/NotionManager";
import NetworkBackground from "@/components/NetworkBackground";
import {
  findPeople,
  searchEvents,
  searchJobs,
  checkHealth,
  LinkedInProfile,
  Event,
  Job,
} from "@/lib/api";

const USER_NAME_STORAGE_KEY = "naj_user_name";
const USER_CONTEXT_STORAGE_KEY = "naj_user_context";
const USER_AI_MODEL_STORAGE_KEY = "naj_ai_model";
const USER_AI_PROVIDER_STORAGE_KEY = "naj_ai_provider";
const USER_AI_BASE_URL_STORAGE_KEY = "naj_ai_base_url";
const USER_AI_API_KEY_SESSION_KEY = "naj_ai_api_key";
const DEFAULT_AI_MODEL = "llama-3.3-70b-versatile";
const DEFAULT_AI_PROVIDER = "groq";

const PEOPLE_LOADING_MESSAGES = [
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

const EVENTS_LOADING_MESSAGES = [
  "Scanning Eventbrite for upcoming conferences...",
  "Checking Meetup for local networking groups...",
  "Browsing ISPOR and ASHEcon event calendars...",
  "Looking for career fairs and industry mixers...",
  "Searching BIO and Biocom event listings...",
  "Digging through conference agendas...",
  "Finding events where the right people gather...",
  "Checking if any free events match your search...",
  "Scrolling through event pages like a pro...",
  "Looking for that perfect networking opportunity...",
  "Hunting down workshops, panels, and roundtables...",
  "Scouting virtual and in-person events...",
  "Pretending to be a regular browser... nothing to see here...",
  "This cat loves a good conference...",
  "Almost there... curating the best events for you...",
];

const JOBS_LOADING_MESSAGES = [
  "Searching Indeed for matching positions...",
  "Checking LinkedIn Jobs for open roles...",
  "Scanning Glassdoor and ZipRecruiter listings...",
  "Browsing BioSpace for pharma and biotech jobs...",
  "Checking Wellfound for startup opportunities...",
  "Looking through BuiltIn for tech-forward roles...",
  "Searching USAJobs for government positions...",
  "Scanning HealthECareers for clinical openings...",
  "Peeking at Craigslist... you never know...",
  "Filtering out the listing pages, keeping the real jobs...",
  "Mining job boards across 14+ sources...",
  "Checking if any positions mention your skills...",
  "Pretending to be a regular browser... nothing to see here...",
  "This cat is a better recruiter than most...",
  "Sorting through results... only the good ones survive...",
  "Almost there... polishing up the best matches...",
];

function SearchLoadingAnimation({ query, type = "people" }: { query?: string; type?: "people" | "events" | "jobs" }) {
  const baseMessages = type === "events" ? EVENTS_LOADING_MESSAGES : type === "jobs" ? JOBS_LOADING_MESSAGES : PEOPLE_LOADING_MESSAGES;
  const [msgIndex, setMsgIndex] = useState(() => Math.floor(Math.random() * baseMessages.length));
  const [dots, setDots] = useState("");

  useEffect(() => {
    const msgTimer = setInterval(() => {
      setMsgIndex((prev) => (prev + 1) % baseMessages.length);
    }, 6000);
    return () => clearInterval(msgTimer);
  }, [baseMessages.length]);

  useEffect(() => {
    const dotTimer = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);
    return () => clearInterval(dotTimer);
  }, []);

  const fieldHint = query?.toLowerCase() || "";
  let fieldMessage: string | null = null;

  if (type === "people") {
    fieldMessage = "Searching for the best connections in your field...";
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
  } else if (type === "events") {
    if (fieldHint.includes("heor") || fieldHint.includes("health econom"))
      fieldMessage = "Looking for HEOR and health economics conferences...";
    else if (fieldHint.includes("pharma") || fieldHint.includes("biotech"))
      fieldMessage = "Searching pharma and biotech industry events...";
    else if (fieldHint.includes("career fair"))
      fieldMessage = "Hunting down the best career fairs near you...";
    else if (fieldHint.includes("meetup") || fieldHint.includes("networking"))
      fieldMessage = "Finding networking meetups and mixers...";
  } else if (type === "jobs") {
    if (fieldHint.includes("heor") || fieldHint.includes("health econom"))
      fieldMessage = "Searching for HEOR and health economics positions...";
    else if (fieldHint.includes("pharma") || fieldHint.includes("biotech"))
      fieldMessage = "Scanning pharma and biotech job boards...";
    else if (fieldHint.includes("remote"))
      fieldMessage = "Looking for remote-friendly positions...";
    else if (fieldHint.includes("data science") || fieldHint.includes("analyst"))
      fieldMessage = "Searching for data and analytics roles...";
    else if (fieldHint.includes("manager") || fieldHint.includes("director"))
      fieldMessage = "Looking for leadership and management positions...";
  }

  const messages = fieldMessage ? [fieldMessage, ...baseMessages] : baseMessages;
  const msg = messages[msgIndex % messages.length];

  return (
    <div className="mt-16 flex flex-col items-center gap-6">
      {/* Lottie cat animation */}
      <div className="w-32 h-32">
        <DotLottieReact
          src="https://assets-v2.lottiefiles.com/a/009fccf8-1171-11ee-b7df-93d19199ced4/AVVma18Z2T.lottie"
          loop
          autoplay
          speed={0.8}
        />
      </div>

      {/* Speech bubble */}
      <div className="bg-white border border-slate-200 rounded-2xl px-6 py-3.5 shadow-sm max-w-md relative">
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white border-l border-t border-slate-200 rotate-45" />
        <p className="text-sm text-slate-600 text-center relative z-10 leading-relaxed">
          {msg}
        </p>
      </div>

      <div className="text-center">
        <p className="text-sm font-medium text-slate-600">
          {type === "events" ? "Searching for events..." : type === "jobs" ? "Searching for jobs..." : "Searching & evaluating profiles..."}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          {type === "events"
            ? "Checking Eventbrite, Meetup, and professional associations"
            : type === "jobs"
            ? `Searching Indeed, LinkedIn, Glassdoor, BioSpace, Wellfound, BuiltIn, and more${dots}`
            : `AI is analyzing each profile. This may take 30-60 seconds${dots}`}
        </p>
      </div>
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
  const peopleGenRef = useRef(0);

  // Events state
  const [events, setEvents] = useState<Event[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [eventsQuery, setEventsQuery] = useState<string | null>(null);
  const [freeOnly, setFreeOnly] = useState(false);
  const eventsGenRef = useRef(0);

  // Jobs state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [jobsQuery, setJobsQuery] = useState<string | null>(null);
  const [remoteOnly, setRemoteOnly] = useState(false);
  const jobsGenRef = useRef(0);

  // User name
  const [userName, setUserName] = useState<string | null>(null);
  const [nameInput, setNameInput] = useState("");
  const [userContext, setUserContext] = useState("");
  const [userContextInput, setUserContextInput] = useState("");
  const [aiModel, setAiModel] = useState(DEFAULT_AI_MODEL);
  const [aiProvider, setAiProvider] = useState(DEFAULT_AI_PROVIDER);
  const [aiBaseUrl, setAiBaseUrl] = useState("");
  const [aiApiKey, setAiApiKey] = useState("");
  const [aiModelInput, setAiModelInput] = useState(DEFAULT_AI_MODEL);
  const [notionConfigured, setNotionConfigured] = useState(true);
  const [notionDefaultDbId, setNotionDefaultDbId] = useState<string | null>(null);

  useEffect(() => {
    checkHealth()
      .then((h) => {
        setNotionConfigured(h.notion_configured);
        setNotionDefaultDbId(h.notion_database_id || null);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const savedName = localStorage.getItem(USER_NAME_STORAGE_KEY);
    const savedContext = localStorage.getItem(USER_CONTEXT_STORAGE_KEY);
    const savedModel = localStorage.getItem(USER_AI_MODEL_STORAGE_KEY);
    const savedProvider = localStorage.getItem(USER_AI_PROVIDER_STORAGE_KEY);
    const savedBaseUrl = localStorage.getItem(USER_AI_BASE_URL_STORAGE_KEY);
    const savedApiKey = sessionStorage.getItem(USER_AI_API_KEY_SESSION_KEY);

    if (savedName) setUserName(savedName);
    if (savedContext) {
      setUserContext(savedContext);
      setUserContextInput(savedContext);
    }
    if (savedModel?.trim()) {
      setAiModel(savedModel.trim());
      setAiModelInput(savedModel.trim());
    }
    if (savedProvider?.trim()) {
      setAiProvider(savedProvider.trim());
    }
    if (savedBaseUrl?.trim()) {
      setAiBaseUrl(savedBaseUrl.trim());
    }
    if (savedApiKey?.trim()) {
      setAiApiKey(savedApiKey.trim());
    }
  }, []);

  const handleSetName = () => {
    const name = nameInput.trim();
    if (!name) return;

    const nextUserContext = userContextInput.trim();
    const nextAiModel = aiModelInput.trim() || DEFAULT_AI_MODEL;
    setUserName(name);
    setUserContext(nextUserContext);
    setAiModel(nextAiModel);
    localStorage.setItem(USER_NAME_STORAGE_KEY, name);
    if (nextUserContext) localStorage.setItem(USER_CONTEXT_STORAGE_KEY, nextUserContext);
    else localStorage.removeItem(USER_CONTEXT_STORAGE_KEY);
    localStorage.setItem(USER_AI_MODEL_STORAGE_KEY, nextAiModel);
  };

  const filteredEvents = freeOnly ? events.filter((e) => e.is_free === true) : events;

  const handlePeopleSearch = async (query: string) => {
    setLastSearchInput(query);
    setPeopleLoading(true);
    setPeopleError(null);
    setProfiles([]);
    setPeopleQuery(null);

    const gen = ++peopleGenRef.current;

    try {
      const result = await findPeople({
        query,
        max_results: 20,
        user_context: userContext || undefined,
        ai_model: aiModel || undefined,
        ai_provider: aiProvider || undefined,
        ai_api_key: aiApiKey || undefined,
        ai_base_url: aiBaseUrl || undefined,
      });
      if (peopleGenRef.current !== gen) return;
      setProfiles(result.profiles);
      setPeopleQuery(result.query_used);
    } catch (e) {
      if (peopleGenRef.current !== gen) return;
      setPeopleError(e instanceof Error ? e.message : "Search failed");
    } finally {
      if (peopleGenRef.current === gen) {
        setPeopleLoading(false);
      }
    }
  };

  const handlePeopleCancel = () => {
    peopleGenRef.current++;
    setPeopleLoading(false);
    setPeopleError(null);
  };

  const handleEventSearch = async (query: string) => {
    setEventsLoading(true);
    setEventsError(null);
    setEvents([]);
    setEventsQuery(null);

    const gen = ++eventsGenRef.current;

    try {
      const result = await searchEvents({
        query,
        max_results: 15,
        user_context: userContext || undefined,
        ai_model: aiModel || undefined,
        ai_provider: aiProvider || undefined,
        ai_api_key: aiApiKey || undefined,
        ai_base_url: aiBaseUrl || undefined,
      });
      if (eventsGenRef.current !== gen) return;
      setEvents(result.events);
      setEventsQuery(result.query_used);
    } catch (e) {
      if (eventsGenRef.current !== gen) return;
      setEventsError(e instanceof Error ? e.message : "Event search failed");
    } finally {
      if (eventsGenRef.current === gen) {
        setEventsLoading(false);
      }
    }
  };

  const handleEventCancel = () => {
    eventsGenRef.current++;
    setEventsLoading(false);
    setEventsError(null);
  };

  const handleJobSearch = async (query: string) => {
    setJobsLoading(true);
    setJobsError(null);
    setJobs([]);
    setJobsQuery(null);

    const gen = ++jobsGenRef.current;

    try {
      const result = await searchJobs({
        query,
        max_results: 25,
        user_context: userContext || undefined,
        ai_model: aiModel || undefined,
        ai_provider: aiProvider || undefined,
        ai_api_key: aiApiKey || undefined,
        ai_base_url: aiBaseUrl || undefined,
      });
      if (jobsGenRef.current !== gen) return;
      setJobs(result.jobs);
      setJobsQuery(result.query_used);
    } catch (e) {
      if (jobsGenRef.current !== gen) return;
      setJobsError(e instanceof Error ? e.message : "Job search failed");
    } finally {
      if (jobsGenRef.current === gen) {
        setJobsLoading(false);
      }
    }
  };

  const handleJobCancel = () => {
    jobsGenRef.current++;
    setJobsLoading(false);
    setJobsError(null);
  };

  const filteredJobs = remoteOnly ? jobs.filter((j) => j.is_remote === true) : jobs;

  const tabConfig = {
    networking: {
      title: "Find the right people to talk to",
      subtitle: "Describe who you're looking for. NAJ searches public profiles, scores relevance with AI, and explains why each person is a good match.",
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
      title: "Search job openings",
      subtitle: "Find job listings across Indeed, LinkedIn, Glassdoor, BioSpace, Wellfound, BuiltIn, USAJobs, Craigslist, and more.",
      placeholder: "Describe the jobs you're looking for...",
      examples: [
        "HEOR analyst positions in pharma",
        "Health economics manager biotech",
        "Real-world evidence scientist remote",
        "Data science healthcare startup jobs",
      ],
    },
  };

  const current = tabConfig[activeTab];
  const isLoading = activeTab === "networking" ? peopleLoading : activeTab === "events" ? eventsLoading : jobsLoading;

  const handleSearch = (query: string) => {
    if (activeTab === "networking") handlePeopleSearch(query);
    else if (activeTab === "events") handleEventSearch(query);
    else if (activeTab === "jobs") handleJobSearch(query);
  };

  const handleCancel = () => {
    if (activeTab === "networking") handlePeopleCancel();
    else if (activeTab === "events") handleEventCancel();
    else if (activeTab === "jobs") handleJobCancel();
  };

  // Welcome screen
  if (!userName) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 relative flex items-center justify-center">
        <NetworkBackground />
        <div className="relative z-[1] max-w-2xl w-full mx-4">
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
            <form
              onSubmit={(e) => { e.preventDefault(); handleSetName(); }}
              className="space-y-4 text-left"
            >
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  What&apos;s your name?
                </label>
                <input
                  type="text"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  placeholder="Enter your first name..."
                  className="w-full px-4 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 bg-white text-slate-800 placeholder-slate-400"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tell NAJ about you and what you need help with
                  <span className="ml-1 text-slate-400 font-normal">(optional)</span>
                </label>
                <textarea
                  value={userContextInput}
                  onChange={(e) => setUserContextInput(e.target.value)}
                  placeholder="Example: I am finishing a PhD in health economics, want to move into HEOR in biotech, prefer West Coast roles, and want help finding people to talk to plus drafting outreach messages."
                  rows={6}
                  className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 bg-white text-slate-800 placeholder-slate-400 resize-y"
                />
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Add as much detail as you want. NAJ will use it to personalize people search, event discovery, and AI-written messages.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  AI model API name
                  <span className="ml-1 text-slate-400 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={aiModelInput}
                  onChange={(e) => setAiModelInput(e.target.value)}
                  placeholder={DEFAULT_AI_MODEL}
                  className="w-full px-4 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 bg-white text-slate-800 placeholder-slate-400"
                />
                <p className="mt-2 text-xs text-slate-400">
                  You can switch this later by clearing your saved profile and entering a new model.
                </p>
              </div>

              <button
                type="submit"
                disabled={!nameInput.trim()}
                className="w-full px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-xl hover:from-indigo-700 hover:to-indigo-600 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 text-sm font-medium transition-all"
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
            <div className="flex items-center gap-2">
              <NotionManager notionConfigured={notionConfigured} defaultPeopleDbId={notionDefaultDbId} onConfigChange={() => {}} />
              <StatusBanner
                aiSettings={{
                  aiModel,
                  aiProvider,
                  aiBaseUrl,
                  aiApiKey,
                }}
                onAiSettingsChange={(next) => {
                  setAiModel(next.aiModel);
                  setAiProvider(next.aiProvider);
                  setAiBaseUrl(next.aiBaseUrl);
                  setAiApiKey(next.aiApiKey);
                }}
              />
            </div>
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

        <SearchBar
          key={activeTab}
          onSearch={handleSearch}
          isLoading={isLoading}
          onCancel={handleCancel}
          placeholder={current.placeholder}
          examples={current.examples}
        />
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

            {eventsLoading && <SearchLoadingAnimation type="events" />}

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

        {/* Jobs results */}
        {activeTab === "jobs" && (
          <>
            {jobsError && (
              <div className="mt-4 bg-red-50 border border-red-200/60 rounded-xl p-4">
                <p className="text-sm text-red-600">{jobsError}</p>
              </div>
            )}

            {jobsQuery && (
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                  <p className="text-sm text-slate-600">
                    <span className="font-semibold text-slate-800">{filteredJobs.length}</span> jobs found
                    {remoteOnly && jobs.length !== filteredJobs.length && (
                      <span className="text-slate-400"> ({jobs.length} total)</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => setRemoteOnly(!remoteOnly)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                    remoteOnly
                      ? "bg-green-50 text-green-700 border-green-200"
                      : "bg-white text-slate-500 border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span>{remoteOnly ? "Showing remote only" : "Show remote only"}</span>
                </button>
              </div>
            )}

            {filteredJobs.length > 0 && (
              <div className="mt-4 space-y-3">
                {filteredJobs.map((job, i) => (
                  <JobCard key={job.url + i} job={job} index={i} />
                ))}
              </div>
            )}

            {jobsLoading && <SearchLoadingAnimation type="jobs" />}

            {!jobsLoading && jobs.length === 0 && !jobsError && !jobsQuery && (
              <div className="mt-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0M12 12.75h.008v.008H12v-.008Z" />
                  </svg>
                </div>
                <p className="text-slate-400 text-sm">Describe the jobs you&apos;re looking for above</p>
              </div>
            )}
          </>
        )}
      </div>

      {chatProfile && (
        <ChatPanel
          profile={chatProfile}
          userContext={userContext}
          aiModel={aiModel}
          aiProvider={aiProvider}
          aiApiKey={aiApiKey}
          aiBaseUrl={aiBaseUrl}
          onClose={() => setChatProfile(null)}
        />
      )}
    </main>
  );
}
