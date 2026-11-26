"""Save the Eyes On Flock API response and extract its Flock portal URLs."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

API_URL = "https://eyesonflock.com/api/v1/data"
PORTAL_PATTERN = re.compile(
    r"https://transparency\.flocksafety\.com/[a-zA-Z0-9_-]+/?"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path, help="New directory for this API snapshot")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Choose a new output directory for each snapshot")

    with urlopen(API_URL, timeout=30) as response:
        raw = response.read()
    retrieved_at = datetime.now(timezone.utc).isoformat()
    payload = json.loads(raw)
    portals = payload.get("portals")
    if not isinstance(portals, list) or not portals:
        raise ValueError("Expected a nonempty portals array in the API response")

    urls = set()
    for record in portals:
        url = record.get("portal_url") if isinstance(record, dict) else None
        if not isinstance(url, str) or not PORTAL_PATTERN.fullmatch(url.strip()):
            raise ValueError("API contains an unexpected portal_url. Inspect its schema.")
        urls.add(url.strip().rstrip("/"))

    summary = payload.get("summary", {})
    metadata = {
        "source_url": API_URL,
        "retrieved_at_utc": retrieved_at,
        "upstream_snapshot_date": summary.get("snapshot_date"),
        "upstream_reported_total": summary.get("total_portals_found"),
        "portal_records": len(portals),
        "distinct_urls": len(urls),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "response.json").write_bytes(raw)
    (args.out / "urls.txt").write_text("\n".join(sorted(urls)) + "\n", encoding="utf-8")
    (args.out / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved {len(urls)} distinct URLs to {args.out / 'urls.txt'}")


if __name__ == "__main__":
    main()
