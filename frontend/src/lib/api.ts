const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SearchQuery {
  query: string;
  location?: string;
  companies?: string[];
  seniority?: string;
  max_results?: number;
}

export interface LinkedInProfile {
  name: string;
  headline: string | null;
  location: string | null;
  linkedin_url: string;
  snippet: string | null;
  relevance_score: number | null;
  relevance_reason: string | null;
}

export interface SearchResponse {
  query_used: string;
  profiles: LinkedInProfile[];
  total_found: number;
}

export interface SaveContactRequest {
  name: string;
  headline?: string;
  location?: string;
  linkedin_url: string;
  relevance_score?: number;
  relevance_reason?: string;
  status?: string;
  notes?: string;
}

export interface EventSearchQuery {
  query: string;
  location?: string;
  max_results?: number;
}

export interface Event {
  title: string;
  url: string;
  date: string | null;
  location: string | null;
  source: string | null;
  description: string | null;
  is_free: boolean | null;
  relevance_score: number | null;
  relevance_reason: number | null;
}

export interface EventSearchResponse {
  query_used: string;
  events: Event[];
  total_found: number;
}

export interface HealthStatus {
  status: string;
  search_configured: boolean;
  notion_configured: boolean;
  ai_configured: boolean;
}

export async function checkHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Backend not reachable");
  return res.json();
}

export async function findPeople(query: SearchQuery): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/search/find-people`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Search failed" }));
    throw new Error(error.detail || "Search failed");
  }
  return res.json();
}

export async function searchEvents(query: EventSearchQuery): Promise<EventSearchResponse> {
  const res = await fetch(`${API_BASE}/api/events/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Event search failed" }));
    throw new Error(error.detail || "Event search failed");
  }
  return res.json();
}

export async function saveContact(contact: SaveContactRequest): Promise<{ status: string; notion_page: { id: string; url: string } }> {
  const res = await fetch(`${API_BASE}/api/search/save-contact`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(contact),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Save failed" }));
    throw new Error(error.detail || "Failed to save contact");
  }
  return res.json();
}
