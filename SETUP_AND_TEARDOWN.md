# NAJ Search Assistant - Setup & Teardown Tracker

Use this document to track everything you created for this project.
When you no longer need the tool, follow the teardown steps to clean up.

---

## How to Start the App

**Terminal 1 -- Backend:**
```
cd C:\Users\nxj561\Desktop\job-search-assistant\backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 -- Frontend:**
```
cd C:\Users\nxj561\Desktop\job-search-assistant\frontend
npm run dev
```

**Then open:** http://localhost:3000

---

## What's Built

| Feature | Status | Description |
|---------|--------|-------------|
| People search | Working | DuckDuckGo search for LinkedIn profiles |
| AI evaluation | Working | Groq scores + explains each profile match |
| Profile enrichment | Working | DDG re-search for experience/education details |
| Notion save | Working | Saves Name, Role, Company, LinkedIn URL, Field, Company Type |
| Events search | Working | 18 sources: ISPOR, ASHEcon, Eventbrite, Meetup, Biocom, etc. |
| Free event filter | Working | Toggle to show only free events |
| Job search | Placeholder | Tab exists, feature not yet built |
| Welcome screen | Working | Asks for name, shows personalized greeting |
| Rate limiter | Working | Max 10 searches/hour to avoid CAPTCHAs |

---

## Accounts & Services Created

### 1. Groq (AI scoring - FREE)
- **Console:** https://console.groq.com/
- **Plan:** Free (30 req/min, 1000 req/day, no expiration)
- **Credit card required:** No
- **API key location:** backend/.env as GROQ_API_KEY

### 2. Notion Integration
- **Integration name:** My Assis sync
- **Managed at:** https://www.notion.so/my-integrations
- **Connected to page:** Informational interviews CA
- **Database used:** "People contacted" (inline database)
- **Columns mapped:** Name, Role, Company, LinkedIn (url), Field (select), Company Type (select)

### 3. Google Cloud Platform (TO BE DEACTIVATED)
- **Project name:** Job-search-assistant
- **Project ID:** job-search-assistant-490519
- **Status:** No longer needed (Google CSE deprecated)
- **Billing account linked:** YES (credit card on file)
- **ACTION REQUIRED:** Follow teardown steps below to remove billing

### 4. Google Gemini API Keys (TO BE DELETED)
- **Key 1:** "Default Gemini API Key" (project 664940699139) - quota was 0
- **Key 2:** "network API Key" (project 239097741989) - quota was 0
- **Managed at:** https://aistudio.google.com/apikey
- **ACTION REQUIRED:** Delete both keys

---

## Local Files with Secrets

| File | Contains | Gitignored? |
|------|----------|-------------|
| `backend/.env` | Notion API key, Groq API key | YES |
| `frontend/.env.local` | Only localhost URL (no secrets) | YES |

---

## Monthly Cost Estimate (while active)

| Service | Free Tier | Risk of charges |
|---------|-----------|-----------------|
| DuckDuckGo search (Playwright) | No API (free forever) | None |
| Groq API | 1000 req/day free | None - hard capped, no billing |
| Notion API | Unlimited (free plan) | None |

**Total monthly cost: $0**

---

## Teardown Checklist (when you're done with the tool)

### Step 1: Google Cloud Platform (DO THIS FIRST - has your credit card)
- [ ] Delete API keys: https://console.cloud.google.com/apis/credentials?project=job-search-assistant-490519
- [ ] Disable Custom Search API: https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=job-search-assistant-490519
- [ ] Unlink billing: Go to billing > linked accounts > disable billing for the project
- [ ] (Optional) Delete project: https://console.cloud.google.com/iam-admin/settings?project=job-search-assistant-490519 > "Shut down"
- [ ] (Optional) Close billing account entirely to remove credit card

### Step 2: Delete Gemini API Keys
- [ ] Go to https://aistudio.google.com/apikey
- [ ] Delete "Default Gemini API Key" (project 664940699139)
- [ ] Delete "network API Key" (project 239097741989)

### Step 3: Delete Programmable Search Engine
- [ ] Go to https://programmablesearchengine.google.com/
- [ ] Delete the search engine you created

### Step 4: Revoke Groq API key
- [ ] Go to https://console.groq.com/ > API Keys
- [ ] Delete or revoke your API key

### Step 5: Revoke Notion integration
- [ ] Go to https://www.notion.so/my-integrations
- [ ] Delete "My Assis sync" integration
- [ ] In Notion, open the Informational Interviews page > "..." > Connections > Remove the integration

### Step 6: Clean up local files
- [ ] Delete `backend/.env` (contains all your secrets)
- [ ] (Optional) Delete the entire project folder
