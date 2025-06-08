import json
import os
import sys
import httpx
import datetime
import hashlib
import hmac

INPUT_JSON = "kindle_plus_books.json"
OUTPUT_HTML = "index.html"

PAAPI_ACCESS_KEY = os.environ.get("AMAZON_PAAPI_ACCESS_KEY")
PAAPI_SECRET_KEY = os.environ.get("AMAZON_PAAPI_SECRET_KEY")
PAAPI_ASSOC_TAG = os.environ.get("AMAZON_PAAPI_ASSOC_TAG")
PAAPI_HOST = "webservices.amazon.co.uk"
PAAPI_REGION = "eu-west-1"
PAAPI_ENDPOINT = f"https://{PAAPI_HOST}/paapi5/getitems"

def extract_asin(item_id):
    return item_id.split('/')[-1]

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_paapi_headers(payload, access_key, secret_key, region, host):
    service = 'ProductAdvertisingAPI'
    amz_date = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    date_stamp = datetime.datetime.utcnow().strftime('%Y%m%d')
    canonical_uri = '/paapi5/getitems'
    canonical_querystring = ''
    canonical_headers = f'content-encoding:amz-1.0\ncontent-type:application/json; charset=utf-8\nhost:{host}\nx-amz-date:{amz_date}\n'
    signed_headers = 'content-encoding;content-type;host;x-amz-date'
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = f'POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
    string_to_sign = f'{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    authorization_header = (
        f'{algorithm} Credential={access_key}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, Signature={signature}'
    )
    return {
        'Content-Encoding': 'amz-1.0',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': host,
        'X-Amz-Date': amz_date,
        'Authorization': authorization_header,
    }

def fetch_paapi_metadata(asin):
    payload = json.dumps({
        "ItemIds": [asin],
        "Resources": [
            "ItemInfo.ContentInfo",
            "ItemInfo.Languages",
            "ItemInfo.Classifications",
        ],
        "PartnerTag": PAAPI_ASSOC_TAG,
        "PartnerType": "Associates"
    })
    headers = get_paapi_headers(payload, PAAPI_ACCESS_KEY, PAAPI_SECRET_KEY, PAAPI_REGION, PAAPI_HOST)
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(PAAPI_ENDPOINT, content=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        item = data.get("ItemsResult", {}).get("Items", [{}])[0]
        info = item.get("ItemInfo", {})
        length = info.get("ContentInfo", {}).get("PagesCount", {}).get("DisplayValue", "")
        language = ""
        lang_obj = info.get("Languages", {}).get("DisplayValues", [])
        if lang_obj:
            language = lang_obj[0].get("DisplayValue", "")
        grade_level = info.get("Classifications", {}).get("GradeLevel", {}).get("DisplayValue", "")
        reading_age = info.get("Classifications", {}).get("ReadingAge", {}).get("DisplayValue", "")
        return {
            "length": length,
            "language": language,
            "grade_level": grade_level,
            "reading_age": reading_age
        }
    except httpx.HTTPStatusError as e:
        print(f"PAAPI error for {asin}: {e}")
        print(f"Response content: {e.response.text}")
        return {
            "length": "",
            "language": "",
            "grade_level": "",
            "reading_age": ""
        }
    except Exception as e:
        print(f"PAAPI error for {asin}: {e}")
        return {
            "length": "",
            "language": "",
            "grade_level": "",
            "reading_age": ""
        }

def main():
    if not (PAAPI_ACCESS_KEY and PAAPI_SECRET_KEY and PAAPI_ASSOC_TAG):
        print("Set AMAZON_PAAPI_ACCESS_KEY, AMAZON_PAAPI_SECRET_KEY, and AMAZON_PAAPI_ASSOC_TAG in your environment.")
        sys.exit(1)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    books = data.get("itemList", [])

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Books Table</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { cursor: pointer; background-color: #f2f2f2; }
        img { max-height: 100px; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/sortable-tablesort@0.2.1/sortable.min.js"></script>
</head>
<body>
    <h1>Books</h1>
    <table class="sortable">
        <thead>
            <tr>
                <th>Cover</th>
                <th>Title</th>
                <th>Reading Age</th>
                <th>Language</th>
                <th>Grade Level</th>
                <th>Length</th>
            </tr>
        </thead>
        <tbody>
'''

    for book in books:
        asin = extract_asin(book.get("itemId", ""))
        title = book.get("title", "")
        cover = book.get("thumbnailUrl", "")
        amazon_url = f"https://www.amazon.co.uk/dp/{asin}"

        meta = fetch_paapi_metadata(asin)
        html += f'''            <tr>
                <td><img src="{cover}" alt="Cover"></td>
                <td><a href="{amazon_url}" target="_blank">{title}</a></td>
                <td>{meta["reading_age"]}</td>
                <td>{meta["language"]}</td>
                <td>{meta["grade_level"]}</td>
                <td>{meta["length"]}</td>
            </tr>
'''

    html += '''        </tbody>
    </table>
    <script>
        Sortable.init();
    </script>
</body>
</html>
'''

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML file generated: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
