import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_html(url: str) -> str:
    """Fetch raw HTML content from the given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def parse_html(html: str):
    """Parse the HTML content and extract specific data."""
    soup = BeautifulSoup(html, 'lxml')  # Use lxml parser for better performance

    # Extract page title
    title = soup.title.string.strip() if soup.title else "No title found"

    # Extract links containing '/player/Dachs'
    links = [a['href'] for a in soup.find_all('a', href=True) if '/player/Dachs' in a['href']]
    for link in links:
        print(link)

    # Extract "Last seen" information
    last_seen_raw = next(
        (row.find_all("td")[1].text.strip()
         for row in soup.find("table", class_="summary").find_all("tr")
         if len(row.find_all("td")) >= 2 and row.find_all("td")[0].text.strip() == "Last seen"),
        "Not found"
    )

    # Clean and parse "Last seen" into ISO 8601 format
    last_seen_cleaned = re.sub(r' as .*', '', last_seen_raw)  # Remove " as Kensei" or similar
    last_seen_iso = ""
    try:
        last_seen_datetime = datetime.strptime(last_seen_cleaned, "%Y-%m-%d %H:%M:%S")
        last_seen_iso = last_seen_datetime.isoformat() + "Z"  # Add 'Z' for UTC
        print(f"Last Seen (ISO 8601): {last_seen_iso}")
    except ValueError:
        print("Error: Unable to parse 'Last seen' value into datetime format.")

def main():
    """Run fetch_html and parse the content."""
    url = "http://www.realmeye.com/player/Dachs"  # Replace with the desired URL
    html_content = fetch_html(url)
    if html_content:
        parse_html(html_content)

if __name__ == "__main__":
    main()