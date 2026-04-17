#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request


def search(query):
    with urllib.request.urlopen(
        f"http://127.0.0.1:8080/search?{urllib.parse.urlencode({'q': query, 'format': 'json'})}",
        timeout=15,
    ) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    return {
        "marker": "[SEARCH RESULTS]",
        "results": [
            {
                "title": r["title"].strip(),
                "url": r["url"].strip(),
                "snippet": (c := r["content"].strip()),
                "type": "search_result",
            }
            for r in data.get("results", [])
        ],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(json.dumps(search(sys.argv[1]), ensure_ascii=False))
