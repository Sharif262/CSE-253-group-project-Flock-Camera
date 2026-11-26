"""Capture a small set of public Flock pages using the observed November layout."""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import TimeoutError as BrowserTimeout, sync_playwright

EXTRACT_FIELDS = """() => [...document.querySelectorAll('#reportContent .tpEntryHeader')]
    .filter(header => header.getClientRects().length)
    .map(header => {
        const value = header.nextElementSibling;
        return {
            label: header.children[0]?.textContent.trim() ?? '',
            description: header.children[1]?.textContent.trim() ?? '',
            value: value?.innerText.trim() ?? '',
            download_present: Boolean(value?.querySelector('a[download]'))
        };
    })"""

CHALLENGE_WAIT_MS = 30000

def retry_delay(header, minimum):
    if header:
        try:
            seconds = int(header)
        except ValueError:
            try:
                date = parsedate_to_datetime(header)
                seconds = (date - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return minimum
        return max(minimum, seconds)
    return minimum

def collect(page, url, out, number, *, already_open=False, retry=0):
    record = {"requested_url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
              "status": "unknown", "fields": []}
    try:
        response = None if already_open else page.goto(
            url, wait_until="domcontentloaded", timeout=30000
        )
        record["already_open"] = already_open
        record["initial_http_status"] = response.status if response else None
        if response and response.status == 429:
            record["retry_after"] = response.headers.get("retry-after")
        challenged = response and response.status == 403 and (
            response.headers.get("cf-mitigated") == "challenge"
            or "just a moment" in page.title().casefold()
        )
        if response and response.status >= 400 and not challenged:
            record["status"] = f"http_{response.status}"
        else:
            marker = page.locator("#reportContent .tpEntryHeader").first.or_(
                page.get_by_role("heading", name="Page not found", exact=True))
            try:
                marker.wait_for(
                    state="visible", timeout=CHALLENGE_WAIT_MS if challenged else 15000
                )
            except BrowserTimeout:
                record["status"] = (
                    "challenge_unresolved" if challenged else "unrecognized_or_not_ready"
                )
            if page.get_by_role("heading", name="Page not found", exact=True).is_visible():
                record["status"] = "page_not_found"
            elif urlsplit(page.url).path.rstrip("/") != urlsplit(url).path.rstrip("/") or (
                urlsplit(page.url).hostname != "transparency.flocksafety.com"
            ):
                record["status"] = "redirect_review"
            elif record["status"] == "unknown":
                record["fields"] = page.evaluate(EXTRACT_FIELDS)
                record["status"] = "fields_extracted" if record["fields"] else "no_fields"
        final = urlsplit(page.url)
        record["final_url"] = final._replace(
            query="" if "__cf_chl" in final.query else final.query
        ).geturl()
        record["title"] = page.title()
        body = page.locator("body").inner_text(timeout=3000)
        update = re.search(r"Last updated:\s*([^\n]+)", body)
        record["page_reported_update"] = update.group(1).strip() if update else None
        suffix = "" if retry == 0 else "-retry" if retry == 1 else f"-retry-{retry}"
        record["evidence"] = f"{number:03d}{suffix}.txt"
        evidence = body.encode()
        (out / record["evidence"]).write_bytes(evidence)
        record["evidence_sha256"] = hashlib.sha256(evidence).hexdigest()
    except Exception as error:
        if record["status"] == "unknown":
            record["status"] = "browser_error"
        record["error"] = str(error)
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", type=Path, help="One reviewed portal URL per line")
    parser.add_argument("out", type=Path, help="Output directory for this batch")
    parser.add_argument("--headed", action="store_true")
    connection = parser.add_mutually_exclusive_group()
    connection.add_argument("--chrome-cdp",
                        help="Loopback DevTools endpoint for an already open Chrome tab")
    connection.add_argument("--existing-chrome", action="store_true",
                            help="Use the endpoint enabled in regular Chrome on macOS")
    parser.add_argument("--resume", action="store_true",
                        help="Continue with URLs that have no recorded attempt")
    parser.add_argument("--delay", type=int, default=30,
                        help="Seconds between portal visits (default: 30)")
    parser.add_argument("--rate-limit-wait", type=int, default=120,
                        help="Minimum seconds before the first HTTP 429 retry (default: 120)")
    parser.add_argument("--rate-limit-retries", type=int, choices=range(4), default=3,
                        help="Maximum retries per URL after HTTP 429 (default: 3)")
    args = parser.parse_args()
    if args.delay < 3 or args.rate_limit_wait < 30:
        parser.error("--delay must be at least 3 and --rate-limit-wait at least 30")
    if args.existing_chrome:
        port_file = Path.home() / "Library/Application Support/Google/Chrome/DevToolsActivePort"
        try:
            port, path = port_file.read_text().splitlines()[:2]
        except (OSError, ValueError):
            parser.error("Chrome endpoint unavailable. Check chrome://inspect/#remote-debugging")
        if not port.isdecimal() or not path.startswith("/devtools/browser/"):
            parser.error("Chrome returned an unexpected DevTools endpoint")
        args.chrome_cdp = f"ws://127.0.0.1:{port}{path}"
    if args.chrome_cdp:
        endpoint = urlsplit(args.chrome_cdp)
        if (endpoint.scheme not in {"http", "ws"} or endpoint.hostname != "127.0.0.1"
                or endpoint.username or endpoint.password or not endpoint.port):
            parser.error("--chrome-cdp requires a local 127.0.0.1 endpoint with a port")
    urls = list(dict.fromkeys(line.strip() for line in args.urls.read_text().splitlines()
                             if line.strip()))
    if not 1 <= len(urls) <= 100 or any(
        not re.fullmatch(r"https://transparency\.flocksafety\.com/[a-zA-Z0-9_-]+/?", url)
        for url in urls
    ):
        parser.error("Supply 1 to 100 reviewed Flock portal URLs")
    log = args.out / "attempts.jsonl"
    start = 0
    if args.resume:
        try:
            attempted = list(dict.fromkeys(json.loads(line)["requested_url"]
                                          for line in log.read_text().splitlines()))
        except (OSError, ValueError, KeyError) as error:
            parser.error(f"Cannot read existing attempts: {error}")
        if attempted != urls[:len(attempted)]:
            parser.error("Existing attempts do not match the start of the input list")
        start = len(attempted)
        if start == len(urls):
            print("All URLs already have a recorded attempt.")
            return
    elif args.out.exists():
        parser.error("Choose a new output directory or use --resume")
    with sync_playwright() as playwright:
        if args.chrome_cdp:
            browser = playwright.chromium.connect_over_cdp(args.chrome_cdp)
            target = urls[start].rstrip("/")
            matches = [tab for context in browser.contexts for tab in context.pages
                       if tab.url.rstrip("/") == target]
            if len(matches) != 1:
                parser.error(f"Open exactly one tab at {target} before attaching")
            page = matches[0]
        else:
            browser = playwright.chromium.launch(headless=not args.headed)
            page = browser.new_page()
        if not args.resume:
            args.out.mkdir(parents=True, exist_ok=False)
        with log.open("a" if args.resume else "x") as output:
            for number, url in enumerate(urls[start:], start + 1):
                record = collect(page, url, args.out, number,
                                 already_open=bool(args.chrome_cdp and number == start + 1))
                output.write(json.dumps(record) + "\n")
                output.flush()
                print(record["status"], url, len(record["fields"]))
                for retry in range(1, args.rate_limit_retries + 1):
                    if record["status"] != "http_429":
                        break
                    minimum = args.rate_limit_wait * 2 ** (retry - 1)
                    wait = retry_delay(record.get("retry_after"), minimum)
                    print(f"Rate limited. Waiting {wait:.0f} seconds before retry "
                          f"{retry}/{args.rate_limit_retries}.",
                          flush=True)
                    time.sleep(wait)
                    record = collect(page, url, args.out, number, retry=retry)
                    output.write(json.dumps(record) + "\n")
                    output.flush()
                    print(record["status"], url, len(record["fields"]))
                if page.is_closed() or not browser.is_connected() or (
                    "target page, context or browser has been closed"
                    in record.get("error", "").casefold()
                ):
                    print("Browser connection closed. Stopped before the next URL.")
                    break
                if "net::ERR_INTERNET_DISCONNECTED" in record.get("error", ""):
                    print("Internet disconnected. Stopped before the next URL.")
                    break
                if record["status"] in {"challenge_unresolved", "http_403", "http_429"} or (
                    "just a moment" in record.get("title", "").casefold()
                ):
                    print("Stopped at an access challenge or rate limit.")
                    break
                if number < len(urls):
                    time.sleep(args.delay)
        if not args.chrome_cdp:
            browser.close()

if __name__ == "__main__":
    main()
