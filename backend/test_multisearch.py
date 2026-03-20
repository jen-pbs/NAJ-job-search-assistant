"""Test the updated multi-search implementation."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.multi_search import search_linkedin_profiles_multi

async def test():
    print("="*70)
    print("Testing Multi-Search: DDG + Ecosia + Brave")
    print("="*70)
    
    try:
        print("\nSearching for: health economist")
        profiles, query_used = await search_linkedin_profiles_multi(
            "health economist",
            max_results=15
        )
        
        print(f"\nFound {len(profiles)} profiles")
        print(f"Query used: {query_used}")
        
        # Show first 5
        for i, p in enumerate(profiles[:5]):
            name = p.name or "[No name]"
            print(f"\n{i+1}. {name}")
            print(f"   LinkedIn: {p.linkedin_url}")
            print(f"   Headline: {p.headline}")
            print(f"   Sources: {', '.join(p.sources)}")
            if p.experience_text:
                print(f"   Experience: {p.experience_text[:100]}")
        
        print("\n" + "="*70)
        print("Test completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
