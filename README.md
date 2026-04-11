# NAJ Search -- Network & Job Assistant

NAJ Search helps you find people to network with, discover professional events, and search for job openings -- all from one place. It searches the public web automatically so you don't have to open dozens of tabs.

## What it does

**Find People** -- Searches across DuckDuckGo, Brave, Bing, and Google for LinkedIn profiles matching your description. Visits public LinkedIn pages for richer data. Optionally uses AI to score how relevant each person is and explain why.

**Discover Events** -- Finds conferences, meetups, career fairs, and networking events from Eventbrite, Meetup, Lu.ma, ISPOR, ASHEcon, BIO, Informa, and more. Shows dates, locations, and whether the event is free or paid.

**Search Jobs** -- Searches 14+ job boards (Indeed, LinkedIn, Glassdoor, ZipRecruiter, BioSpace, Wellfound, BuiltIn, USAJobs, and others). Visits each job page to extract company, salary, location, and posting date.

**Save to Notion** -- Connect your Notion workspace to save people, jobs, or events directly to your databases.

**AI Chat** -- Draft outreach messages and get networking advice using any AI provider (Groq, OpenAI, OpenRouter, or your own).

## What you need

- **Python 3.10+** (for the backend)
- **Node.js 18+** (for the frontend)
- **Chrome or Chromium** (Playwright uses it to search the web)

Everything else is optional:
- A **Groq, OpenAI, or OpenRouter API key** if you want AI features (scoring, chat, smart search). You can set this up later in the app.
- A **Notion API key** if you want to save results to Notion. Also optional.

## How to set it up

### 1. Clone the project

```
git clone https://github.com/jen-pbs/NAJ-job-search-assistant.git
cd NAJ-job-search-assistant
```

### 2. Set up the backend

```
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

Install dependencies:
```
pip install -r requirements.txt
playwright install chromium
```

### 3. Set up the frontend

Open a new terminal:
```
cd frontend
npm install
```

### 4. Configure API keys (optional)

Copy the example file and add your keys:
```
cp .env.example backend/.env
```

Open `backend/.env` in any text editor and fill in the keys you have:

```
# Optional -- for saving to Notion
NOTION_API_KEY=ntn_your_key_here
NOTION_DATABASE_ID=your_database_id_here

# Optional -- for AI features (scoring, chat)
# You can also set this later in the app UI
GROQ_API_KEY=your_groq_key_here
```

You don't need any keys to search. The app works without them -- you just won't have AI scoring or Notion saving until you add them.

**Where to get keys:**
- **Groq** (free): Go to [console.groq.com](https://console.groq.com/), sign up, and create an API key
- **Notion**: Go to [notion.so/my-integrations](https://www.notion.so/my-integrations), create an integration, and copy the secret. Then share your Notion database with the integration.
- **OpenAI / OpenRouter**: Sign up at their websites and create an API key. You can enter these directly in the app's "Update model" button -- no `.env` needed.

### 5. Start the app

Start the backend (from the `backend` folder):
```
uvicorn app.main:app --reload
```

Start the frontend (from the `frontend` folder):
```
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## How to use it

1. **Enter your name** and optionally describe your background (this helps AI personalize results)
2. **Pick a tab** -- People, Events, or Jobs
3. **Type what you're looking for** and hit search
4. **Browse results** -- click "Apply" or "View" to open the original page
5. **Save to Notion** -- click the Notion button in the header to connect your databases, then use the "Save" button on any result

## Switching AI providers

Click the **"Update model"** button in the top-right corner. You can enter:
- A provider name (groq, openai, openrouter, or any OpenAI-compatible provider)
- Your API key
- A custom base URL (optional for known providers)
- A model name (e.g. `llama-3.3-70b-versatile`, `gpt-4o`, `anthropic/claude-3.5-sonnet`)

The API key is stored in your browser session only -- it's never saved to disk or sent anywhere except the AI provider you chose.

## Connecting Notion

1. Click the **"Notion"** button in the top-right corner
2. If you have `NOTION_API_KEY` in your `.env`, your databases will load automatically
3. Assign databases to **People**, **Jobs**, or **Events** by clicking the icons next to each database
4. A "Save" button will appear on result cards for any category that has a database assigned

The app automatically maps your data to matching Notion columns (Name, Company, URL, Date, etc.). It works with any database structure -- you don't need specific column names.

## Project structure

```
backend/          Python API (FastAPI)
  app/
    routers/      API endpoints (search, events, jobs, chat, notion)
    services/     Search engines, AI scoring, Notion client
    models/       Data models
frontend/         Web interface (Next.js + Tailwind)
  src/
    app/          Main page
    components/   UI components (cards, search bar, chat panel)
    lib/          API client
```

## Troubleshooting

**"Backend offline" message** -- Make sure `uvicorn app.main:app --reload` is running in the backend folder.

**No search results** -- The app uses Playwright to search DuckDuckGo. Make sure you ran `playwright install chromium`. If DuckDuckGo is rate-limiting your IP, wait a few minutes and try again.

**Notion not connecting** -- Make sure your Notion integration has access to the database. In Notion, open the database page, click the `...` menu, go to "Connections", and add your integration.

**AI features not working** -- Check that your API key is correct. Groq's free tier has rate limits (30 requests/minute). If you hit the limit, wait a minute or switch to a different provider.
