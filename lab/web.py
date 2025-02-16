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
        self.visited_urls_by_user = {}
        self.clicked_elements_by_user = {}
        self.current_user = None
        self.request_counter = 0
        self.network_log = []
        self.logout_keywords = ['logout', 'sign out', 'signout']
        self.login_keywords = ['login', 'log-in', 'signin', 'sign-in']
        self.base_url = re.match(r'https?://[^/]+', start_url).group(0)
        
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
        
        self.ignore_patterns = [
            r'\.js$',
            r'\.css$',
            r'\.png$',
            r'\.jpg$',
            r'\.jpeg$',
            r'\.gif$',
            r'\.ico$',
            r'\.woff2?$',
            r'\.ttf$',
            r'\.eot$',
            r'\.svg$',
            r'/static/',
            r'/assets/',
            r'/favicon\.ico$',
            r'/sockjs-node/',
            r'/webpack/',
            r'hot-update\.js',
            r'hot-update\.json'
        ]
        
        self.include_patterns = [
            r'/api/',
            r'/auth/',
            r'/graphql',
            r'/login',
            r'/logout',
            r'/signup'
        ]

    def load_credentials(self, credentials_file: str) -> List[Dict[str, str]]:
        credentials = [
            {
                'username': 'dr_smith',
                'password': 'doctor123',
                'role': 'doctor'
            },
            {
                'username': 'john_doe',
                'password': 'patient123',
                'role': 'patient'
            },
            {
                'username': 'jane_smith',
                'password': 'patient456',
                'role': 'patient'
            }
        ]
        
        print(f"📋 Loaded {len(credentials)} sets of credentials")
        for cred in credentials:
            print(f"  - {cred['username']} ({cred['role']})")
        return credentials

    def should_log_request(self, url: str, resource_type: str) -> bool:
        if resource_type in ['stylesheet', 'image', 'font', 'other']:
            return False
            
        if any(re.search(pattern, url) for pattern in self.ignore_patterns):
            return False
            
        if self.include_patterns:
            return any(re.search(pattern, url) for pattern in self.include_patterns)
            
        return True

    def filter_request_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        return {
            k.lower(): v for k, v in headers.items() 
            if k.lower() in self.important_request_headers
        }

    async def log_request(self, request: Request):
        if not self.should_log_request(request.url, request.resource_type):
            return
            
        self.request_counter += 1
        request_id = self.request_counter
        
        headers = self.filter_request_headers(request.headers)
        
        body = None
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                post_data = await request.post_data()
                if post_data:
                    try:
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
        
        self.network_log.append(request_data)
        print(f"📡 Request #{request_id}: {request.method} {request.url}")
        if body:
            print(f"📦 Request Body: {json.dumps(body, indent=2)}")

    async def log_response(self, response):
        request = response['request']
        
        if not self.should_log_request(request.url, request.resource_type):
            return
        
        for entry in self.network_log:
            if entry['request']['url'] == request.url and 'response' not in entry:
                headers = dict(response['headers'])
                
                body = response['body']
                if body and 'application/json' in response['headers'].get('content-type', ''):
                    try:
                        body = json.loads(body)
                        body = json.dumps(body, indent=2)
                    except:
                        pass
                
                entry['response'] = {
                    'status': response['status'],
                    'status_text': response['status_text'],
                    'headers': headers,
                    'body': body
                }
                print(f"📨 Response #{entry['id']}: {response['status']} {request.url}")
                if body:
                    print(f"📦 Response Body: {body}")
                break

    async def route_handler(self, route):
        request = route.request
        
        try:
            response = await route.fetch()
            
            await self.log_request(request)
            
            response_body = None
            try:
                response_body = await response.text()
            except Exception as e:
                print(f"⚠️ Failed to get response body: {str(e)}")
            
            response_with_request = {
                'url': request.url,
                'status': response.status,
                'status_text': response.status_text,
                'headers': response.headers,
                'body': response_body,
                'request': request
            }
            
            await self.log_response(response_with_request)
            
            await route.fulfill(response=response)
            
        except Exception as e:
            print(f"❌ Error in route handler: {str(e)}")
            await route.continue_()

    async def wait_for_app_load(self, page: Page):
        try:
            await page.wait_for_selector('#root > *', timeout=3000)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error waiting for app load: {e}")

    async def is_login_page(self, page: Page) -> bool:
        content = await page.content()
        content = content.lower()
        
        return any(keyword in page.url.lower() or keyword in content 
                  for keyword in self.login_keywords)

    async def handle_login(self, page: Page, credentials: Dict[str, str]):
        print(f"\n🔑 Attempting login with credentials: {credentials['username']} (role: {credentials['role']})")
        
        username_selector = 'input[type="text"]'
        password_selector = 'input[type="password"]'
        
        try:
            await page.fill(username_selector, credentials['username'])
            print(f"✍️ Filled username field using selector: {username_selector}")
            
            await page.fill(password_selector, credentials['password'])
            print(f"✍️ Filled password field using selector: {password_selector}")
            
            await page.click('button[type="submit"]')
            
            await asyncio.sleep(2)
            
            if await self.is_logged_in(page):
                print(f"✅ Successfully logged in as {credentials['username']} ({credentials['role']})")
                return True
            else:
                print(f"❌ Login failed for {credentials['username']}")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False

    async def is_logged_in(self, page: Page) -> bool:
        try:
            await page.wait_for_selector('button:has-text("Logout")', timeout=1000)
            return True
        except:
            return False

    async def find_logout_button(self, page: Page) -> bool:
        await self.wait_for_app_load(page)
        
        logout_selectors = [
            'button:has-text("Logout")',
            'button:has-text("Log out")',
            'button:has-text("Sign out")',
            'a:has-text("Logout")',
            'a:has-text("Log out")',
            'a:has-text("Sign out")',
            '[role="button"]:has-text("Logout")',
            '[role="button"]:has-text("Log out")',
            'button.logout-button',
            '#logout-button',
            '[aria-label*="logout" i]',
            '[aria-label*="log out" i]',
            '[data-testid*="logout"]',
            '*:has-text("Logout")',
            '*:has-text("Log out")',
            '*:has-text("Sign out")'
        ]
        
        for selector in logout_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    print(f"🚪 Found logout element with selector: {selector}")
                    if await element.is_visible() and await element.is_enabled():
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        if await self.is_login_page(page):
                            print("✅ Successfully logged out")
                            return True
            except Exception as e:
                continue
        return False

    async def handle_logout(self, page: Page):
        if not await self.find_logout_button(page):
            print("❌ Failed to find logout button")

    async def fill_form(self, page: Page, element_id: str):
        try:
            print("📝 Filling form fields...")
            
            await page.wait_for_selector('[role="dialog"]', timeout=1000)
            await asyncio.sleep(1)
            
            try:
                await page.fill('div[role="dialog"] input[type="text"]', 'Blood Test')
                print("✅ Filled Test Type field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Test Type: {str(e)}")
            
            try:
                await page.fill('div[role="dialog"] textarea', 'Normal Range - 120/80')
                print("✅ Filled Result field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Result: {str(e)}")
            
            try:
                await page.fill('div[role="dialog"] input[type="date"]', '2025-02-16')
                print("✅ Filled Date field")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Failed to fill Date: {str(e)}")
            
            submit_button = await page.wait_for_selector('div[role="dialog"] button:has-text("Add Test Result")', timeout=1000)
            if submit_button:
                await asyncio.sleep(1)
                await submit_button.click()
                await page.wait_for_load_state('networkidle', timeout=3000)
                print("✅ Submitted form")
                
                try:
                    await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=3000)
                    print("✅ Dialog closed")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"⚠️ Dialog might not have closed: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ Error filling form: {str(e)}")

    async def get_clickable_elements(self, page: Page) -> list:
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
                await page.wait_for_selector(selector, timeout=1000)
                elements.extend(await page.query_selector_all(selector))
            except:
                continue
        return elements

    async def get_element_identifier(self, element) -> str:
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
        links = []
        try:
            anchors = await page.query_selector_all('a[href]')
            for anchor in anchors:
                href = await anchor.get_attribute('href')
                text = await anchor.text_content()
                if href:
                    if href.startswith('/'):
                        href = f"{self.base_url}{href}"
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
        self.current_user = credentials['username']
