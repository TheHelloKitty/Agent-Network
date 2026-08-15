from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch the browser (set headless=False to see it)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Go to a website
        page.goto("https://payhip.com/login")

        # Example: fill login form
        # page.fill('input[type="email"]', "your-email@example.com")
        # page.fill('input[type="password"]', "your-password")
        # page.click('button[type="submit"]')

        # Keep browser open for a few seconds so you can see it
        page.wait_for_timeout(5000)

        browser.close()

if __name__ == "__main__":
    main()
