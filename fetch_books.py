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
    all_items = []
    page_number = 1
    next_page_token = None

    while True:
        response_data = fetch_catalog_items(next_page_token)
        all_items.extend(response_data.get("itemList", []))

        print(f"Fetched page {page_number} with {len(response_data.get('itemList', []))} items")

        if response_data.get("lastPage", False):
            print("Reached last page")
            break

        next_page_token = response_data.get("nextPageToken")
        if not next_page_token:
            print("No next page token found")
            break

        page_number += 1

    # Save merged result
    with open("kindle_plus_books.json", "w", encoding="utf-8") as f:
        json.dump({"itemList": all_items}, f, indent=2)
    print(f"Saved {len(all_items)} titles to kindle_plus_books.json")


if __name__ == "__main__":
    if not COOKIES:
        print("Fill out the COOKIES dict with your session cookies.")
        sys.exit(1)

    fetch_all_catalog_items()
