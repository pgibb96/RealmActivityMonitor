import requests
from bs4 import BeautifulSoup
import os
import boto3
from datetime import datetime
import re
from dateutil.parser import isoparse
from boto3.dynamodb.conditions import Key
import json


# Helper used to retrieve specific secure variables from AWS SSM Parameter Store
def get_secure_variable(link: str):
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=f"/discord/{link}", WithDecryption=True)
    return response["Parameter"]["Value"]


# Load the secure variables
discord_id = get_secure_variable("id")
boss_id = get_secure_variable("id/boss")
realmeye_url = get_secure_variable("realmeye")
realmeye_headers = get_secure_variable("realmeye/header")


# Main hanlder
def lambda_handler(event, context):
    print("Lambda function started.")
    response = get_realmeye_html()
    if response is None:
        return {"statusCode": 500, "body": "Failed to fetch data from RealmEye."}
    print("Fetched RealmEye HTML successfully.")

    # Parse the HTML to find "Last seen"
    last_seen_raw = parse_realmeye_html(response)

    # Clean and parse "Last seen" into ISO 8601 format
    last_seen = format_raw_last_seen(last_seen_raw)
    if not last_seen:
        return {"statusCode": 400, "body": "Invalid 'Last seen' format."}

    # Get dynamoDB table name from environment variable
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    if not table_name:
        return {"statusCode": 500, "body": "DynamoDB table name not configured."}
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # Get existing data (get single item by PlayerName)
    existing_timestamp = ""
    existing_strike = 0
    existing_cooldown = 0
    try:
        response = table.get_item(Key={"PlayerName": "Dachs"})
        item = response.get("Item")
        if item:
            existing_timestamp = item.get("Timestamp", "")
            existing_strike = item.get("Strike", 0)
            existing_cooldown = item.get("CooldownCounter", 0)
            print(
                f"Existing timestamp: {existing_timestamp}, Existing strike: {existing_strike}, existing cooldown: {existing_cooldown}"
            )
    except Exception as e:
        print(f"Error fetching existing item: {e}")

    if not existing_timestamp:
        print("No existing timestamp found, treating as new entry.")

    # Compare timestamps
    strike = existing_strike
    cooldown_counter = existing_cooldown
    try:
        if existing_timestamp:
            existing_dt = isoparse(existing_timestamp)
            new_dt = isoparse(last_seen)
            print(
                f"Comparing existing timestamp {existing_dt} with new timestamp {new_dt}"
            )
            # If new activity, increment strike and reset cooldown
            if new_dt > existing_dt:
                strike += 1 if strike < 5 else 0  # Cap strikes at 5
                cooldown_counter = 0
            # If on a cooldown, increment cooldown counter
            elif strike > 0:
                cooldown_counter += 1
                if cooldown_counter >= 12:
                    strike = 0  # Reset strike if new timestamp is not later
                    cooldown_counter = 0  # Reset cooldown
            # If no new activity, everything has been going well
            else:
                print(f"Good job, you are staying strong")
        else:
            strike = 0  # No previous timestamp, so treat as new
            cooldown_counter = 0  # Reset cooldown
    except Exception as e:
        print(f"Error comparing timestamps: {e}")
        strike = 0  # Fallback to safe default
        cooldown_counter = 0  # Reset cooldown

    print(f"New strike number: {strike}, cooldown counter: {cooldown_counter}")

    # Update DynamoDB only if something has changed
    if existing_timestamp and (
        existing_timestamp != last_seen
        or existing_strike != strike
        or existing_cooldown != cooldown_counter
    ):
        table.put_item(
            Item={
                "PlayerName": "Dachs",
                "Timestamp": last_seen,
                "Strike": strike,
                "CooldownCounter": cooldown_counter,
            }
        )
        print(f"Last seen value saved: {last_seen}")

    if strike != existing_strike:
        notify_discord(last_seen, strike)
    return {
        "statusCode": 200,
        "body": f"Last seen value saved: {last_seen}, strike number: {strike}",
    }


def get_realmeye_html():
    url = realmeye_url
    headers = {
        "User-Agent": realmeye_headers,
    }
    response = requests.get(url, headers=headers, timeout=10)
    try:
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    return response.text


def parse_realmeye_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    last_seen_raw = "Not found"
    table = soup.find("table", class_="summary")
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 2 and cells[0].text.strip() == "Last seen":
            last_seen_raw = cells[1].text.strip()
            break
    return last_seen_raw


def format_raw_last_seen(raw_last_seen: str):
    if raw_last_seen == "Hidden":
        print(f"Hmmm, being sneaky I see...")
    # Remove " as Kensei" or similar suffix
    cleaned = re.sub(r" as .*", "", raw_last_seen)
    # Convert to ISO 8601 format
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat() + "Z"  # Add 'Z' for UTC
    except ValueError:
        print(f"Error parsing last seen: {cleaned}")
        return ""

def generate_message(last_seen: str, strike: int):
    # Good job
    if strike == 0:
        return f"<:bufoblessback:1393766628365303878> Pray you stay on the right path, <@{discord_id}>"
    # Strike 1
    if strike == 1:
        return f"<a:bufoalarma:1393766625462980649> BUSTED! <@{discord_id}> was spotted <t:{int(datetime.fromisoformat(last_seen.replace('Z', '')).timestamp())}:R>. Let's hope you choose a better path. This behavior will not be tolerated..."
    # Strike 2
    if strike == 2:
        return f"<:tsabufogropesyou:1393770044449886340> <@{discord_id}>, you have continued to be play. Explain yourself, or face the consequences!"
    # Strike 3, you're out!
    if strike == 3:
        return f"<:bufobehindbars:1393766626922332282> <@{discord_id}>, you have defied me for the last time.\n<@{boss_id}> has been informed of this continued transgression."
    # Strike 4, clown
    if strike == 4:
        return f"<:bufoclown:1393766629644697721> <-- This you, <@{discord_id}>?"

    return f"<:bufocometothedarkside:1393766630970097664> Welcome back, <@{discord_id}>"


# Discord notification function
def notify_discord(last_seen: str, strike: int):
    webhook_url = get_secure_variable("webhook")
    if not webhook_url:
        print("No Discord webhook URL configured.")
        return
    content = generate_message(last_seen, strike)
    message = {"content": content, "allowed_mentions": {"users": [discord_id, boss_id]}}

    try:
        resp = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        resp.raise_for_status()
        print("Notification sent to Discord.")
    except requests.RequestException as e:
        print(f"Failed to send Discord notification: {e}")
