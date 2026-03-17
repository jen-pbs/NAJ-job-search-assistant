# Job Search Assistant - Setup & Teardown Tracker

Use this document to track everything you created for this project.
When you no longer need the tool, follow the teardown steps to clean up.

---

## Accounts & Services Created

### 1. Brave Search API
- **Dashboard:** https://api-dashboard.search.brave.com/
- **Plan:** Free (2000 queries/month)
- **Credit card required:** No
- **API key location:** backend/.env as BRAVE_API_KEY

### 2. Notion Integration
- **Integration name:** My Assis sync
- **Managed at:** https://www.notion.so/my-integrations
- **Connected to page:** Informational interviews CA
- **Database used:** "People contacted" (inline database)

### 3. OpenAI (optional, not set up yet)
- **Status:** Not configured
- **Would be used for:** AI query interpretation and relevance scoring
- **Sign up at:** https://platform.openai.com/

### 4. Google Cloud Platform (TO BE DEACTIVATED)
- **Project name:** Job-search-assistant
- **Project ID:** job-search-assistant-490519
- **Status:** API was deprecated by Google, no longer needed
- **Billing account linked:** YES (credit card on file)
- **ACTION REQUIRED:** Follow teardown steps below to remove billing

---

## Local Files with Secrets

| File | Contains | Gitignored? |
|------|----------|-------------|
| `backend/.env` | Notion API key, Brave API key | YES |
| `frontend/.env.local` | Only localhost URL (no secrets) | YES |

---

## Monthly Cost Estimate (while active)

| Service | Free Tier | Risk of charges |
|---------|-----------|-----------------|
| Brave Search API | 2000 queries/month free | None on free plan |
| Notion API | Unlimited (free plan) | None |
| OpenAI (if added) | No free tier | Pay-per-use. gpt-4o-mini ~$0.15/1M tokens. Expect <$1/month. |

---

## Teardown Checklist (when you're done with the tool)

### Step 1: Google Cloud Platform (DO THIS FIRST - has your credit card)
- [ ] Delete API keys: https://console.cloud.google.com/apis/credentials?project=job-search-assistant-490519
- [ ] Disable Custom Search API: https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=job-search-assistant-490519
- [ ] Unlink billing: Go to billing > linked accounts > disable billing for the project
- [ ] (Optional) Delete project: https://console.cloud.google.com/iam-admin/settings?project=job-search-assistant-490519 > "Shut down"
- [ ] (Optional) Close billing account entirely to remove credit card

### Step 2: Delete Programmable Search Engine
- [ ] Go to https://programmablesearchengine.google.com/
- [ ] Delete the search engine you created

### Step 3: Brave Search API
- [ ] Go to https://api-dashboard.search.brave.com/
- [ ] Delete your API key or close your account

### Step 4: Revoke Notion integration
- [ ] Go to https://www.notion.so/my-integrations
- [ ] Delete "My Assis sync" integration
- [ ] In Notion, open the Informational Interviews page > "..." > Connections > Remove the integration

### Step 5: Revoke OpenAI key (if created)
- [ ] Go to https://platform.openai.com/api-keys
- [ ] Delete the API key

### Step 6: Clean up local files
- [ ] Delete `backend/.env` (contains all your secrets)
- [ ] (Optional) Delete the entire project folder
