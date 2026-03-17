from app.services.web_search import _search_google_sync, parse_linkedin_result

results = _search_google_sync('site:linkedin.com/in "HEOR"', max_results=5)
print(f"Found {len(results)} raw results")
for r in results[:3]:
    print(f"  - {r['title'][:80]}")
    profile = parse_linkedin_result(r)
    if profile:
        print(f"    Name: {profile.name}, Headline: {profile.headline}")
