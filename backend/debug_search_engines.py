"""Debug script to inspect actual DOM structure of search engines."""
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

def debug_bing():
    """Inspect Bing's actual HTML structure."""
    print("\n" + "="*60)
    print("DEBUGGING BING")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            query = "HEOR director site:linkedin.com/in"
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=30"
            print(f"\nSearching: {url}")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.5, 4.0))
            
            # Save page content for inspection
            with open("bing_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("✓ Page content saved to bing_page.html")
            
            # Try to find LinkedIn links
            all_links = page.locator("a[href*='linkedin.com/in/']")
            print(f"\n✓ Found {all_links.count()} LinkedIn links via selector 'a[href*=\"linkedin.com/in/\"]'")
            
            # Check parent containers
            print("\n--- Checking parent containers ---")
            for i in range(min(3, all_links.count())):
                link = all_links.nth(i)
                href = link.get_attribute("href")
                print(f"\nLink {i+1}: {href}")
                
                # Try to get surrounding HTML
                try:
                    parent = link.locator("xpath=ancestor::li[1]")
                    if parent.count() > 0:
                        print(f"  Parent <li>: {parent.inner_text()[:200]}...")
                    else:
                        parent = link.locator("xpath=ancestor::div[1]")
                        print(f"  Parent <div> classes: {parent.get_attribute('class')}")
                except:
                    pass
            
            # Check for other selectors that might work
            print("\n--- Alternative selectors ---")
            li_count = page.locator("li").count()
            print(f"Total <li> elements: {li_count}")
            
            ol_count = page.locator("ol#b_results").count()
            print(f"<ol#b_results> containers: {ol_count}")
            
            if ol_count > 0:
                li_in_ol = page.locator("ol#b_results li").count()
                print(f"<li> elements inside ol#b_results: {li_in_ol}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            input("\n[Press Enter to close browser]")
            browser.close()

def debug_google():
    """Inspect Google's actual HTML structure."""
    print("\n" + "="*60)
    print("DEBUGGING GOOGLE")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=USER_AGENT)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()
        
        try:
            query = "HEOR director site:linkedin.com/in"
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=30"
            print(f"\nSearching: {url}")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 4.0))
            
            # Check for CAPTCHA
            content = page.content()
            if "captcha" in content.lower() or "unusual traffic" in content.lower():
                print("⚠ CAPTCHA or unusual traffic message detected")
                with open("google_captcha.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("✓ CAPTCHA page saved to google_captcha.html")
                browser.close()
                return
            
            # Save page content for inspection
            with open("google_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("✓ Page content saved to google_page.html")
            
            # Try to find LinkedIn links
            all_links = page.locator("a[href*='linkedin.com/in/']")
            print(f"\n✓ Found {all_links.count()} LinkedIn links")
            
            # Check result containers
            print("\n--- Result containers ---")
            items_divg = page.locator("div.g").count()
            print(f"<div.g> (old style): {items_divg}")
            
            items_sokoban = page.locator("div[data-sokoban-container]").count()
            print(f"<div[data-sokoban-container]>: {items_sokoban}")
            
            # Find first LinkedIn result
            if all_links.count() > 0:
                print("\n--- First LinkedIn result details ---")
                link = all_links.first
                href = link.get_attribute("href")
                print(f"Href: {href}")
                
                # Get parent g div
                try:
                    parent_g = link.locator("xpath=ancestor::div[@class='g'][1]")
                    if parent_g.count() > 0:
                        print(f"Parent <div.g> content: {parent_g.inner_text()[:300]}...")
                except:
                    pass
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            input("\n[Press Enter to close browser]")
            browser.close()

if __name__ == "__main__":
    print("Search Engine Debug Tool")
    print("This will open real browsers so you can inspect HTML")
    print("\nChoose which to debug:")
    print("1. Bing")
    print("2. Google")
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        debug_bing()
    elif choice == "2":
        debug_google()
    else:
        print("Invalid choice")
