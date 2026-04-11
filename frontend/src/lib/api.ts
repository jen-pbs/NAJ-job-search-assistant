const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SearchQuery {
  query: string;
  location?: string;
  companies?: string[];
  seniority?: string;
  max_results?: number;
  user_context?: string;
  ai_model?: string;
  ai_provider?: string;
  ai_api_key?: string;
  ai_base_url?: string;
}

export interface LinkedInProfile {
  name: string;
  headline: string | null;
  location: string | null;
  linkedin_url: string;
  snippet: string | null;
  relevance_score: number | null;
  relevance_reason: string | null;
  company: string | null;
  role_title: string | null;
  field: string | null;
  company_type: string | null;
  saved_in_notion?: boolean;
  notion_page_url?: string | null;
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
  company?: string;
  role_title?: string;
  status?: string;
  notes?: string;
  field?: string;
  company_type?: string;
}

export interface EventSearchQuery {
  query: string;
  location?: string;
  max_results?: number;
  user_context?: string;
  ai_model?: string;
  ai_provider?: string;
  ai_api_key?: string;
  ai_base_url?: string;
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

export interface JobSearchQuery {
  query: string;
  location?: string;
  max_results?: number;
  user_context?: string;
  ai_model?: string;
  ai_provider?: string;
  ai_api_key?: string;
  ai_base_url?: string;
}

export interface Job {
  title: string;
  company: string | null;
  url: string;
  location: string | null;
  salary: string | null;
  date_posted: string | null;
  source: string | null;
  description: string | null;
  is_remote: boolean | null;
}

export interface JobSearchResponse {
  query_used: string;
  jobs: Job[];
  total_found: number;
}

export interface HealthStatus {
  status: string;
  search_configured: boolean;
  notion_configured: boolean;
  notion_database_id: string | null;
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

export async function searchJobs(query: JobSearchQuery): Promise<JobSearchResponse> {
  const res = await fetch(`${API_BASE}/api/jobs/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Job search failed" }));
    throw new Error(error.detail || "Job search failed");
  }
  return res.json();
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function sendChatMessage(
  messages: ChatMessage[],
  profileContext?: string,
  userContext?: string,
  aiModel?: string,
  aiProvider?: string,
  aiApiKey?: string,
  aiBaseUrl?: string,
  onChunk?: (text: string) => void,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      profile_context: profileContext,
      user_context: userContext,
      ai_model: aiModel,
      ai_provider: aiProvider,
      ai_api_key: aiApiKey,
      ai_base_url: aiBaseUrl,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Chat failed" }));
    throw new Error(error.detail || "Chat failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  let full = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    full += chunk;
    onChunk?.(full);
  }
  return full;
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

// ---------------------------------------------------------------------------
// Notion database management
// ---------------------------------------------------------------------------

export interface NotionDatabase {
  id: string;
  title: string;
  url: string;
  columns: Record<string, string>;
}

export interface NotionSchema {
  title: string;
  properties: Record<string, { type: string; id: string; options?: string[] }>;
}

export async function listNotionDatabases(apiKey?: string): Promise<NotionDatabase[]> {
  const res = await fetch(`${API_BASE}/api/notion/databases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey || "" }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to list databases" }));
    throw new Error(error.detail || "Failed to list databases");
  }
  const data = await res.json();
  return data.databases;
}

export async function getNotionSchema(databaseId: string, apiKey?: string): Promise<NotionSchema> {
  const res = await fetch(`${API_BASE}/api/notion/schema`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey || "", database_id: databaseId }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to get schema" }));
    throw new Error(error.detail || "Failed to get schema");
  }
  return res.json();
}

export async function saveToNotion(
  databaseId: string,
  fields: Record<string, string | number | boolean>,
  apiKey?: string,
): Promise<{ status: string; notion_page: { id: string; url: string } }> {
  const res = await fetch(`${API_BASE}/api/notion/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey || "", database_id: databaseId, fields }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to save" }));
    throw new Error(error.detail || "Failed to save to Notion");
  }
  return res.json();
}
