import json

# Path to your JSON file
INPUT_JSON = "kindle_plus_books.json"
OUTPUT_HTML = "index.html"

def extract_asin(item_id):
    # Example: "//amazon-book/B00HNXBRFE" -> "B00HNXBRFE"
    return item_id.split('/')[-1]

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    books = data.get("itemList", [])

    # Start HTML
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
    <!-- SortableJS -->
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
    <!-- Sortable Table library (tofsjonas.github.io/sortable/) -->
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sortable-tablesort@0.2.1/sortable.min.js"></script>
</head>
<body>
    <h1>Books</h1>
    <table class="sortable">
        <thead>
            <tr>
                <th>Cover</th>
                <th>Title</th>
            </tr>
        </thead>
        <tbody>
'''

    for book in books:
        asin = extract_asin(book.get("itemId", ""))
        title = book.get("title", "")
        cover = book.get("thumbnailUrl", "")
        amazon_url = f"https://www.amazon.co.uk/dp/{asin}"

        html += f'''            <tr>
                <td><img src="{cover}" alt="Cover"></td>
                <td><a href="{amazon_url}" target="_blank">{title}</a></td>
            </tr>
'''

    html += '''        </tbody>
    </table>
    <script>
        // Initialize sortable table
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
