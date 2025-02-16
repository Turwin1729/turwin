# Web Application Crawler

This is an automated web application crawler that uses Playwright to explore websites, automatically handle login pages, fill forms, and track all HTTP requests and responses in real-time.

## Features

- 🔍 Automatic login page detection and handling
- 🤖 Automated form filling with test data
- 🖱️ Automatic button and link clicking
- 📊 Real-time request/response monitoring
- 🌐 Visual browser automation (non-headless mode)
- 🔄 Smart navigation with backtracking

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Create a `.env` file with your login credentials:
```
LOGIN_USERNAME=your_username
LOGIN_PASSWORD=your_password
```

## Usage

1. Edit the `web_crawler.py` file and set your target URL in the `main()` function:
```python
target_url = "http://your-target-website.com"
```

2. Run the crawler:
```bash
python web_crawler.py
```

The crawler will:
- Open a visible browser window
- Navigate to the target URL
- Automatically detect and handle login pages
- Fill forms with test data
- Click buttons and links
- Print all HTTP requests and responses in real-time
- Track visited pages

## Output

The crawler provides real-time feedback in the terminal:
- 🔄 Outgoing requests
- 📥 Incoming responses
- ✍️ Form filling actions
- 🖱️ Button clicks
- 📍 Page navigation

## Customization

You can customize the crawler's behavior by modifying:
- Login detection keywords in `login_keywords`
- Form filling test data in `fill_form()`
- Clickable element selectors in `click_buttons()`
- Request/response logging in `log_request()` and `log_response()`
