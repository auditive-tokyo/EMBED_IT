import requests
import json
import csv
import os

def webpilot(webpilot_url, webpilot_output=None):
    # If no output file name is provided, use a default one
    if not webpilot_output:
        webpilot_output = 'webpilot'
    url = "https://webreader.webpilotai.com/api/visit-web"
    headers = {
        "Content-Type": "application/json",
        "WebPilot-Friend-UID": "secret_user"
    }

    data = {
        "link": webpilot_url,
        "user_has_request": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    # The response will be a JSON object containing a summary of the web page
    summary = response.json()

    # Extract the title, url, and text
    title = summary.get('title')
    if not title and 'meta' in summary:
        title = summary['meta'].get('og:title')
    if not title:
        title = 'No title'

    url = data['link']
    text = summary['content']

    # Remove the title from the text
    text = text.replace(title, '')

    # Prepare the output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    # Write the title, url, and text to a CSV file in the output directory
    with open(os.path.join(output_dir, f'{webpilot_output}.csv'), 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['title', 'url', 'text'])
        writer.writerow([title, url, text])