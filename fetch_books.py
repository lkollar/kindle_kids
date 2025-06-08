import json
from pathlib import Path
import sys

import httpx

COOKIES = {}

def fetch_catalog_items(next_page_token=None):
    url = "https://parents.amazon.co.uk/ajax/get-catalog-items"

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
    }

    # Export cookies from browser, logged in to parents.amazon.co.uk

    # Filter Kindle books only
    payload = {
        "contentTypeFilterList": ["EBOOK"],
        "deviceFamilyFilterList": ["E_READER"],
        "childDirectedIdFilter": None,
        "subscriptionPresent": True,
        "searchQuery": None,
        "nextPageToken": next_page_token,
    }

    with httpx.Client() as client:
        response = client.post(url, headers=headers, cookies=COOKIES, json=payload)
        return response.json()


def fetch_all_catalog_items():
    output_dir = Path("catalog_responses")
    output_dir.mkdir(exist_ok=True)

    page_number = 1
    next_page_token = None

    while True:
        response_data = fetch_catalog_items(next_page_token)

        output_file = output_dir / f"catalog_page_{page_number:03d}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2)

        print(f"Saved page {page_number} to {output_file}")

        if response_data.get("lastPage", False):
            print("Reached last page")
            break

        next_page_token = response_data.get("nextPageToken")
        if not next_page_token:
            print("No next page token found")
            break

        page_number += 1


if __name__ == "__main__":
    if not COOKIES:
        print("Fill out the COOKIES dict with your session cookies.")
        sys.exit(1)

    fetch_all_catalog_items()
