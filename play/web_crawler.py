import asyncio
import csv
import json
import re
from datetime import datetime
from typing import Dict, List, Set
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Page, Request, Response

load_dotenv()

class WebCrawler:
    def __init__(self, start_url: str, credentials_file: str):
        self.start_url = start_url
        self.credentials = self.load_credentials(credentials_file)
        self.visited_urls_by_user = {}  # Initialize empty dict
        self.clicked_elements_by_user = {}  # Initialize empty dict
        self.current_user = None
        self.request_counter = 0
        self.network_log = []
        self.logout_keywords = ['logout', 'sign out', 'signout']
        self.login_keywords = ['login', 'log-in', 'signin', 'sign-in']
        self.base_url = re.match(r'https?://[^/]+', start_url).group(0)
        
        # Headers to keep in request logs
        self.important_request_headers = {
            'authorization',
            'cookie',
            'x-csrf-token',
            'content-type',
            'content-length',
            'host',
            'origin',
            'x-requested-with',
            'x-api-key',
            'api-key',
            'token',
            'access-token',
            'refresh-token',
            'session-id',
            'x-session-id'
        }
        
        # Define patterns for requests to ignore
        self.ignore_patterns = [
            r'\.js$',          # JavaScript files
            r'\.css$',         # CSS files
            r'\.png$',         # Images
            r'\.jpg$',
            r'\.jpeg$',
            r'\.gif$',
            r'\.ico$',
            r'\.woff2?$',      # Fonts
            r'\.ttf$',
            r'\.eot$',
            r'\.svg$',
            r'/static/',       # Static resources
            r'/assets/',
            r'/favicon\.ico$',
            r'/sockjs-node/',  # Development server
            r'/webpack/',
            r'hot-update\.js',
            r'hot-update\.json'
        ]
        
        # Define patterns for requests to include
        self.include_patterns = [
            r'/api/',          # API endpoints
            r'/auth/',         # Auth endpoints
            r'/graphql',       # GraphQL if used
            r'/login',         # Authentication
            r'/logout',
            r'/signup'
        ]

    def should_log_request(self, url: str, resource_type: str) -> bool:
        """Determine if a request should be logged based on URL and resource type"""
        # Always ignore certain resource types
        if resource_type in ['stylesheet', 'image', 'font', 'other']:
            return False
            
        # Check if URL matches any ignore patterns
        if any(re.search(pattern, url) for pattern in self.ignore_patterns):
            return False
            
        # If we have any include patterns, at least one must match
        if self.include_patterns:
            return any(re.search(pattern, url) for pattern in self.include_patterns)
            
        return True

    def load_credentials(self, credentials_file: str) -> List[Dict[str, str]]:
        """Load credentials from CSV file"""
        credentials = []
        try:
            with open(credentials_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    credentials.append(row)
                    # Initialize tracking sets for each user
                    username = row['username']
                    self.visited_urls_by_user[username] = set()
                    self.clicked_elements_by_user[username] = set()
            print(f"📝 Loaded {len(credentials)} sets of credentials")
        except Exception as e:
            print(f"⚠️ Error loading credentials: {e}")
        return credentials

    def filter_request_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter request headers to keep only important ones"""
        return {
            k.lower(): v for k, v in headers.items() 
            if k.lower() in self.important_request_headers
        }

    async def log_request(self, request: Request):
        """Log request details"""
        # Skip if we shouldn't log this request
        if not self.should_log_request(request.url, request.resource_type):
            return
            
        self.request_counter += 1
        request_id = self.request_counter
        
        # Get and filter request headers
        headers = self.filter_request_headers(request.headers)
        
        # Get request body if it exists
        body = None
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                post_data = request.post_data
                if post_data:
                    try:
                        # Try to decode as JSON if it's JSON content
                        if 'application/json' in request.headers.get('content-type', ''):
                            body = json.loads(post_data)
                        else:
                            body = post_data
                    except:
                        body = post_data
        except Exception as e:
            print(f"⚠️ Failed to get request body: {str(e)}")
            body = None
        
        request_data = {
            'id': request_id,
            'timestamp': datetime.now().isoformat(),
            'request': {
                'url': request.url,
                'method': request.method,
                'headers': headers,
                'post_data': body,
                'resource_type': request.resource_type
            }
        }
        
        # Store request data temporarily
        self.network_log.append(request_data)
        print(f"📡 Request #{request_id}: {request.method} {request.url}")
        if body:
            print(f"📦 Request Body: {json.dumps(body, indent=2)}")

    async def log_response(self, response: Response):
        """Log response details"""
        request = response.request
        
        # Skip if we shouldn't log this request
        if not self.should_log_request(request.url, request.resource_type):
            return
        
        # Find the corresponding request in our log
        for entry in self.network_log:
            if entry['request']['url'] == request.url and 'response' not in entry:
                # Get response headers (keep all response headers)
                headers = dict(response.headers)
                
                # Always try to get response body
                try:
                    body = await response.text()
                    # If it's JSON, parse it to make it readable
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            body = json.loads(body)
                            body = json.dumps(body, indent=2)
                        except:
                            pass
                except Exception as e:
                    print(f"⚠️ Failed to get response body for {request.url}: {str(e)}")
                    body = None
                
                # Add response data to the existing entry
                entry['response'] = {
                    'status': response.status,
                    'status_text': response.status_text,
                    'headers': headers,
                    'body': body
                }
                print(f"📨 Response #{entry['id']}: {response.status} {response.url}")
                if body:
                    print(f"📦 Response Body: {body}")
                break

    async def wait_for_app_load(self, page: Page):
        """Wait for React app to load and render"""
        try:
            # Reduced timeout and wait time
            await page.wait_for_selector('#root > *', timeout=3000)
            await asyncio.sleep(0.5)  # Reduced from 2s to 0.5s
        except Exception as e:
            print(f"⚠️ Error waiting for app load: {e}")

    async def is_login_page(self, page: Page) -> bool:
        """Detect if current page is a login page"""
        content = await page.content()
        content = content.lower()
        
        # Check URL and content for login-related keywords
        return any(keyword in page.url.lower() or keyword in content 
                  for keyword in self.login_keywords)

    async def handle_login(self, page: Page, credentials: Dict[str, str]):
        """Handle login process"""
        print(f"\n🔑 Attempting login with credentials: {credentials['username']} (role: {credentials['role']})")
        
        # Fill login form
        username_selector = 'input[type="text"]'
        password_selector = 'input[type="password"]'
        
        try:
            # Fill username
            await page.fill(username_selector, credentials['username'])
            print(f"✍️ Filled username field using selector: {username_selector}")
            
            # Fill password
            await page.fill(password_selector, credentials['password'])
            print(f"✍️ Filled password field using selector: {password_selector}")
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for navigation
            await asyncio.sleep(2)
            
            # Check if login was successful
            if await self.is_logged_in(page):
                print(f"✅ Successfully logged in as {credentials['username']} ({credentials['role']})")
                return True
            else:
                print(f"❌ Login failed for {credentials['username']}")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False

    async def route_handler(self, route):
        """Handle route interception for request/response logging"""
        request = route.request
        
        try:
            # Continue the route and get response
            response = await route.fetch()
            
            # Log request and response
            await self.log_request(request)
            await self.log_response(response)
            
            # Continue with the response
            await route.fulfill(response=response)
            
        except Exception as e:
            print(f"❌ Error in route handler: {str(e)}")
            await route.continue_()

    async def is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in"""
        # Check for logout button
        try:
            await page.wait_for_selector('button:has-text("Logout")', timeout=1000)
            return True
        except:
            return False

    async def find_logout_button(self, page: Page) -> bool:
        """Find and click logout button"""
        await self.wait_for_app_load(page)
        
        logout_selectors = [
            # Common logout button patterns
            'button:has-text("Logout")',
            'button:has-text("Log out")',
            'button:has-text("Sign out")',
            'a:has-text("Logout")',
            'a:has-text("Log out")',
            'a:has-text("Sign out")',
            # More specific selectors
            '[role="button"]:has-text("Logout")',
            '[role="button"]:has-text("Log out")',
            'button.logout-button',
            '#logout-button',
            '[aria-label*="logout" i]',
            '[aria-label*="log out" i]',
            '[data-testid*="logout"]',
            # Look for any element containing logout text
            '*:has-text("Logout")',
            '*:has-text("Log out")',
            '*:has-text("Sign out")'
        ]
        
        for selector in logout_selectors:
            try:
                # First try to find the element
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    print(f"🚪 Found logout element with selector: {selector}")
                    # Make sure element is visible and clickable
                    if await element.is_visible() and await element.is_enabled():
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        # Verify we're logged out by checking for login page
                        if await self.is_login_page(page):
                            print("✅ Successfully logged out")
                            return True
            except Exception as e:
                continue
        return False

    async def handle_logout(self, page: Page):
        """Handle logout"""
        if not await self.find_logout_button(page):
            print("❌ Failed to find logout button")

    async def fill_form(self, page: Page, element_id: str):
        """Fill a form with test data"""
        try:
            print("📝 Filling form fields...")
            
            # Wait for the dialog to be fully visible
            await page.wait_for_selector('[role="dialog"]', timeout=1000)
            await asyncio.sleep(1)  # Wait for dialog animation
            
            # Try to fill Test Type
            try:
                await page.fill('div[role="dialog"] input[type="text"]', 'Blood Test')
                print("✅ Filled Test Type field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Test Type: {str(e)}")
            
            # Try to fill Result
            try:
                await page.fill('div[role="dialog"] textarea', 'Normal Range - 120/80')
                print("✅ Filled Result field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Result: {str(e)}")
            
            # Try to fill Date
            try:
                await page.fill('div[role="dialog"] input[type="date"]', '2025-02-16')
                print("✅ Filled Date field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Date: {str(e)}")
            
            # Look for submit button and click it
            submit_button = await page.wait_for_selector('div[role="dialog"] button:has-text("Add Test Result")', timeout=1000)
            if submit_button:
                await asyncio.sleep(1)  # Wait before clicking
                await submit_button.click()
                await page.wait_for_load_state('networkidle', timeout=3000)
                print("✅ Submitted form")
                
                # Wait for dialog to close
                try:
                    await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=3000)
                    print("✅ Dialog closed")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"⚠️ Dialog might not have closed: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ Error filling form: {str(e)}")

    async def get_clickable_elements(self, page: Page) -> list:
        """Get all clickable elements on the page"""
        await self.wait_for_app_load(page)
        
        selectors = [
            'button',
            'a[href]',
            '[role="button"]',
            '[onclick]',
            'input[type="submit"]',
            'input[type="button"]',
            '.btn',
            '.button',
            '[class*="button"]',
            '[class*="btn"]',
            '[tabindex]:not([tabindex="-1"])',
            '[role="link"]',
            '[role="menuitem"]',
            '[role="tab"]'
        ]
        
        elements = []
        for selector in selectors:
            try:
                # Wait for elements to be available
                await page.wait_for_selector(selector, timeout=1000)
                elements.extend(await page.query_selector_all(selector))
            except:
                continue
        return elements

    async def get_element_identifier(self, element) -> str:
        """Create a unique identifier for an element"""
        try:
            tag = await element.evaluate('el => el.tagName')
            text = (await element.text_content() or '').strip()
            href = await element.get_attribute('href') or ''
            id_attr = await element.get_attribute('id') or ''
            classes = await element.get_attribute('class') or ''
            return f"{tag}|{text}|{href}|{id_attr}|{classes}"
        except:
            return ''

    async def get_all_links(self, page: Page) -> list:
        """Get all links on the page"""
        links = []
        try:
            # Get all anchor tags
            anchors = await page.query_selector_all('a[href]')
            for anchor in anchors:
                href = await anchor.get_attribute('href')
                text = await anchor.text_content()
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = f"{self.base_url}{href}"
                    # Only include links that are part of the same domain
                    if href.startswith(self.base_url):
                        links.append({
                            'href': href,
                            'text': text.strip(),
                            'element': anchor
                        })
        except Exception as e:
            print(f"Error getting links: {e}")
        return links

    async def explore_as_user(self, page: Page, credentials: Dict[str, str]):
        """Explore the site as a specific user"""
        self.current_user = credentials['username']
        print(f"\n👤 Exploring as user: {self.current_user}")
        
        # Initialize tracking for this user if not exists
        if self.current_user not in self.visited_urls_by_user:
            self.visited_urls_by_user[self.current_user] = set()
        
        # Navigate to start URL
        print(f"🌐 Navigating to {self.start_url}")
        await page.goto(self.start_url)
        await self.wait_for_app_load(page)
        await asyncio.sleep(1)  # 1 second delay after navigation
        
        # Login
        if not await self.handle_login(page, credentials):
            print(f"❌ Failed to login as {self.current_user}")
            return
        
        # Explore the site
        await self.explore_page(page)
        
        print(f"\n⏳ Waiting 10 seconds before logout...")
        await asyncio.sleep(10)  # 10 second delay before logout
        
        # Logout
        await self.handle_logout(page)
        
        # Wait for logout to complete
        await asyncio.sleep(2)

    async def explore_page(self, page: Page, depth: int = 0, max_depth: int = 5):
        """Explore a single page by clicking all clickable elements"""
        if depth >= max_depth:
            return
        
        print(f"\n🔍 Exploring page: {page.url} (depth: {depth})")
        
        # Store current URL to detect navigation
        current_url = page.url
        
        # Get all clickable elements
        clickable_elements = await page.query_selector_all('a, button, input[type="submit"]')
        clicked_elements = set()
        
        for element in clickable_elements:
            try:
                # Skip if already clicked
                element_id = await element.evaluate('element => element.outerHTML')
                if element_id in clicked_elements:
                    continue
                
                # Get element text and attributes for better logging
                element_text = await element.text_content()
                element_type = await element.evaluate('element => element.tagName.toLowerCase()')
                
                # Skip logout button
                if element_text and any(keyword in element_text.lower() for keyword in ['logout', 'sign out']):
                    continue
                
                print(f"🖱️ Clicking {element_type}: {element_text or 'unnamed element'}")
                
                # Store pre-click URL to detect navigation
                pre_click_url = page.url
                
                # Click the element
                await element.click(timeout=1000)
                await page.wait_for_load_state('networkidle', timeout=3000)
                await asyncio.sleep(1)  # 1 second delay after each click
                
                # Mark this element as clicked
                clicked_elements.add(element_id)
                
                # Check if a modal dialog appeared
                modal = await page.query_selector('.modal, [role="dialog"], .dialog')
                if modal:
                    print(f"📝 Found modal dialog after clicking {element_text}")
                    await self.fill_form(page, element_id)
                    # Wait for modal to close
                    await page.wait_for_selector('.modal, [role="dialog"], .dialog', state='hidden', timeout=3000)
                    await page.wait_for_load_state('networkidle', timeout=3000)
                    await asyncio.sleep(1)  # 1 second delay after modal interaction
                
                # If URL changed, explore the new page
                if page.url != pre_click_url:
                    self.visited_urls_by_user[self.current_user].add(page.url)
                    await self.explore_page(page, depth + 1, max_depth)
                    # Go back if we navigated away
                    if page.url != pre_click_url:
                        await page.goto(pre_click_url)
                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(1)  # 1 second delay after navigation
                
            except Exception as e:
                print(f"⚠️ Failed to interact with element: {str(e)}")
                continue

    def get_visited_urls(self) -> Set[str]:
        """Get visited URLs for current user"""
        return self.visited_urls_by_user.get(self.current_user, set())

    def get_clicked_elements(self) -> Set[str]:
        """Get clicked elements for current user"""
        return self.clicked_elements_by_user.get(self.current_user, set())

    async def run(self):
        """Run the web crawler"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Set to True for headless mode
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Create a new page
            page = await context.new_page()
            
            # Set up request interception
            await page.route("**/*", self.route_handler)
            
            # Explore with each set of credentials
            for credentials in self.credentials:
                await self.explore_as_user(page, credentials)
                
                # Print pages visited by this user
                print(f"\nPages visited by user {credentials['username']}:")
                if credentials['username'] in self.visited_urls_by_user:
                    for url in self.visited_urls_by_user[credentials['username']]:
                        print(f"  - {url}")
                else:
                    print("  No pages visited")
                
                print("\n---\n")  # Separator between users
            
            # Save network log
            log_file = self.save_network_log()
            print(f"\nNetwork log saved to: {log_file}")
            
            print("\nKeeping browser open for 5 seconds...")
            await asyncio.sleep(5)
            
            await browser.close()

    def save_network_log(self):
        """Save the network log to a JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'network_log_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump({
                'metadata': {
                    'start_url': self.start_url,
                    'timestamp': datetime.now().isoformat(),
                    'total_requests': self.request_counter
                },
                'requests': self.network_log
            }, f, indent=2)
        
        print(f"\n💾 Saved network log to {filename}")
        return filename

async def main():
    # Replace with your target website
    target_url = "http://localhost:3000/"
    credentials_file = "credentials.csv"
    crawler = WebCrawler(target_url, credentials_file)
    await crawler.run()

if __name__ == "__main__":
    asyncio.run(main())
