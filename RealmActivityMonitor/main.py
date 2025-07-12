import requests

def fetch_html(url: str) -> str:
    """Fetch raw HTML content from the given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def main():
    """Run fetch_html with a sample URL."""
    url = "https://example.com"  # Replace with the desired URL
    html_content = fetch_html(url)
    if html_content:
        print(f"Fetched content from {url}:\n{html_content[:200]}...")  # Print the first 200 characters

if __name__ == "__main__":
    main()