import requests
from bs4 import BeautifulSoup
import os
import boto3
from datetime import datetime
import re

def lambda_handler(event, context):
    url = "https://www.realmeye.com/player/Dachs"

    """Fetch raw HTML content from the given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    try:
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {"statusCode": 500, "body": "Error fetching data"}

    soup = BeautifulSoup(response.text, "lxml")
    last_seen_raw = "Not found"
    table = soup.find("table", class_="summary")
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 2 and cells[0].text.strip() == "Last seen":
            last_seen_raw = cells[1].text.strip()
            break
    # Clean and parse "Last seen" into ISO 8601 format
    last_seen_cleaned = re.sub(r' as .*', '', last_seen_raw)  # Remove " as Kensei" or similar
    last_seen = ""
    try:
        last_seen_datetime = datetime.strptime(last_seen_cleaned, "%Y-%m-%d %H:%M:%S")
        last_seen_iso = last_seen_datetime.isoformat() + "Z"  # Add 'Z' for UTC
        print(f"Last Seen (ISO 8601): {last_seen_iso}")
    except ValueError:
        print("Error: Unable to parse 'Last seen' value into datetime format.")

    # Save to DynamoDB
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    table.put_item(Item={"PlayerName": "Dachs", "LastSeen": last_seen})
    print (f"Last seen value saved: {last_seen}")
    return {
        "statusCode": 200,
        "body": f"Last seen value saved: {last_seen}"
    }