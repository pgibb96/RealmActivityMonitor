import requests
from bs4 import BeautifulSoup
import os
import boto3
from datetime import datetime
import re
from dateutil.parser import isoparse
from boto3.dynamodb.conditions import Key
import json

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

    soup = BeautifulSoup(response.text, "html.parser")
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
        last_seen = last_seen_datetime.isoformat() + "Z"  # Add 'Z' for UTC
        print(f"Last Seen (ISO 8601): {last_seen}")
    except ValueError:
        print("Error: Unable to parse 'Last seen' value into datetime format.")

    # Save to DynamoDB with comparison
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # Get existing data (fetch latest Timestamp for PlayerName)
    existing_timestamp = ""
    try:
        response = table.query(
            KeyConditionExpression=Key("PlayerName").eq("Dachs"),
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get("Items", [])
        existing_timestamp = items[0]["Timestamp"] if items else ""
        print(f"Existing timestamp: {existing_timestamp}")
    except Exception as e:
        print(f"Error fetching existing item: {e}")

    # Compare timestamps
    isActive = False
    try:
        if existing_timestamp:
            existing_dt = isoparse(existing_timestamp)
            new_dt = isoparse(last_seen)
            if new_dt > existing_dt:
                isActive = True
        else:
            isActive = True  # No previous timestamp, so treat as new
    except Exception as e:
        print(f"Error comparing timestamps: {e}")
        isActive = True  # Fallback to safe default

    print(f"isActive: {isActive}")

    # Update DynamoDB
    table.put_item(Item={
        "PlayerName": "Dachs",
        "Timestamp": last_seen,
        "isActive": isActive
    })

    print(f"Last seen value saved: {last_seen}")
    if isActive:
        notify_discord(last_seen)
    return {
        "statusCode": 200,
        "body": f"Last seen value saved: {last_seen}, isActive: {isActive}"
    }

def get_webhook_url():
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(
        Name="/discord/webhook",
        WithDecryption=True
    )
    return response["Parameter"]["Value"]

# Discord notification function
def notify_discord(last_seen: str):
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("No Discord webhook URL configured.")
        return

    message = {
        "content": f"🟢 BUSTED! @Dachs was active <t:{int(datetime.fromisoformat(last_seen.replace('Z', '')).timestamp())}:R>.\nAdding @sophievolpe for visibility"
    }

    try:
        resp = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        resp.raise_for_status()
        print("Notification sent to Discord.")
    except requests.RequestException as e:
        print(f"Failed to send Discord notification: {e}")

