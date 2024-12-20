import http.cookiejar as cookiejar
import cloudscraper

# Path to your exported cookie file
cookie_file_path = "./data/cookies/f95_cookies.txt"

# Load cookies from the Netscape file
jar = cookiejar.MozillaCookieJar(cookie_file_path)
jar.load(ignore_discard=True, ignore_expires=True)

# Convert to dictionary for cloudscraper
cookies = {cookie.name: cookie.value for cookie in jar}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://f95zone.to/threads/cosy-cafe-v0-11-cosy-creator.143711/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers",
}

# Initialize cloudscraper with cookies and headers
scraper = cloudscraper.create_scraper()
response = scraper.get(
    "https://f95zone.to/threads/cosy-cafe-v0-11-cosy-creator.143711/",
    cookies=cookies,
    headers=headers
)

# Check if the response indicates success
if response.status_code == 200:
    print("Authenticated request successful!")
    with open("page_content.html", "w", encoding="utf-8") as file:
        file.write(response.text)
else:
    print(f"Request failed with status code: {response.status_code}")
