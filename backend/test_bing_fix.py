"""Test the updated Bing search implementation."""
import time
import random
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = {runtime: {}};
"""

def test_bing_new():
    """Test new Bing implementation without site:linkedin.com/in"""
    print("\n" + "="*60)
    print("TESTING NEW BING IMPLEMENTATION")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            # Test 1: Remove site syntax and add "linkedin"
            query = "HEOR director linkedin"
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=50"
            print(f"\nQuery: {query}")
            print(f"URL: {url}\n")
            
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            # Try new selector strategy
            ol_results = page.locator("ol#b_results li")
            print(f"<ol#b_results li> elements found: {ol_results.count()}")
            
            if ol_results.count() > 0:
                print("\nSearching for LinkedIn links in results...")
                linkedin_found = 0
                
                for i in range(min(10, ol_results.count())):
                    item = ol_results.nth(i)
                    links = item.locator("a[href*='linkedin.com']")
                    
                    if links.count() > 0:
                        for j in range(links.count()):
                            href = links.nth(j).get_attribute("href")
                            if "linkedin.com/in/" in href:
                                linkedin_found += 1
                                print(f"  {linkedin_found}. {href[:80]}")
                                if linkedin_found >= 5:
                                    break
                    if linkedin_found >= 5:
                        break
                
                if linkedin_found == 0:
                    print("  (No direct LinkedIn profile links found in first 10 results)")
                else:
                    print(f"\nSuccess! Found {linkedin_found} LinkedIn profile links")
            else:
                print("No results container found")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

def test_ecosia():
    """Test new Ecosia search engine."""
    print("\n" + "="*60)
    print("TESTING ECOSIA (Google replacement)")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            query = "HEOR director linkedin"
            url = f"https://www.ecosia.org/search?q={query.replace(' ', '+')}"
            print(f"\nQuery: {query}")
            print(f"URL: {url}\n")
            
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            # Check for results container
            results_section = page.locator("section.results")
            print(f"Results container found: {results_section.count() > 0}")
            
            items = page.locator("article")
            print(f"Article elements found: {items.count()}")
            
            if items.count() > 0:
                print("\nSearching for LinkedIn links...")
                linkedin_found = 0
                
                for i in range(min(10, items.count())):
                    item = items.nth(i)
                    links = item.locator("a[href*='linkedin.com']")
                    
                    if links.count() > 0:
                        for j in range(links.count()):
                            href = links.nth(j).get_attribute("href")
                            if "linkedin.com/in/" in href:
                                linkedin_found += 1
                                print(f"  {linkedin_found}. {href[:80]}")
                                if linkedin_found >= 5:
                                    break
                    if linkedin_found >= 5:
                        break
                
                if linkedin_found > 0:
                    print(f"\nSuccess! Found {linkedin_found} LinkedIn profile links on Ecosia")
                else:
                    print("  (No LinkedIn profile links found in first 10 results)")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    test_bing_new()
    test_ecosia()
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
