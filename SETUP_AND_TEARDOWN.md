# Job Search Assistant - Setup & Teardown Tracker

Use this document to track everything you created for this project.
When you no longer need the tool, follow the teardown steps to clean up.

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

### 3. Google Cloud Platform (TO BE DEACTIVATED)
- **Project name:** Job-search-assistant
- **Project ID:** job-search-assistant-490519
- **Status:** API was deprecated by Google, no longer needed
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
| Playwright search | No API (free forever) | None |
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
