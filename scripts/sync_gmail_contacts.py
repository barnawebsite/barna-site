"""
Send the current member list to the BARNA Gmail account's contacts.

The other half is scripts/gmail-contacts-sync.gs, a Google Apps Script web app
in the barna.socialnetworks@gmail.com account. This reads Memberstack and POSTs
it names, emails and a status; the Apps Script does the contact edits. That
split keeps the Memberstack key here on GitHub, out of a Gmail account that
volunteers sign in to.

Status per member:
  active  has any ACTIVE plan (board, legacy and website members alike)
  past    no active plan, but did have one: a website plan now cancelled, or a
          legacy member whose accessexpiresat date has passed
Anyone with no plan at all and no expiry date is left out: that is someone
who started signing up and never paid, not a member.

Dry run by default: the Apps Script reports what it would do and changes
nothing. Set CONTACTS_SYNC_LIVE_MODE=true to make the changes.

Required environment variables:
  MEMBERSTACK_SECRET_KEY   Memberstack Admin API key, Live mode
  CONTACTS_SYNC_URL        the Apps Script web app URL (.../exec). Treat it as
                           a secret: it is the only thing guarding the script.
"""
import json
import os
import sys
import urllib.request

BASE_URL = "https://admin.memberstack.com"


def require_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"\nERROR: {name} is not set, so the contacts sync cannot run.\n")
    return value


API_KEY = require_env("MEMBERSTACK_SECRET_KEY")
SYNC_URL = require_env("CONTACTS_SYNC_URL")
LIVE = os.environ.get("CONTACTS_SYNC_LIVE_MODE", "").strip().lower() == "true"


def fetch_all_members():
    members, end_param = [], ""
    while True:
        req = urllib.request.Request(
            f"{BASE_URL}/members?limit=50{end_param}",
            headers={"X-API-KEY": API_KEY, "Accept": "application/json",
                     "User-Agent": "Mozilla/5.0 (compatible; BARNA-contacts-sync/1.0)"},
        )
        with urllib.request.urlopen(req) as resp:
            page = json.loads(resp.read().decode(errors="replace"))
        members.extend(page["data"])
        if not page.get("hasNextPage"):
            return members
        end_param = f"&after={page['endCursor']}"


def status(member):
    plans = member.get("planConnections", [])
    if any(p.get("status") == "ACTIVE" for p in plans):
        return "active"
    if plans or (member.get("customFields") or {}).get("accessexpiresat"):
        return "past"
    return None


def main():
    rows = []
    for m in fetch_all_members():
        s = status(m)
        if not s:
            continue
        cf = m.get("customFields") or {}
        rows.append({"email": m["auth"]["email"], "status": s,
                     "first": (cf.get("first-name") or "").strip(),
                     "last": (cf.get("last-name") or "").strip()})

    n_active = sum(r["status"] == "active" for r in rows)
    print(f"Mode: {'LIVE' if LIVE else 'DRY RUN'}")
    print(f"Sending {n_active} active and {len(rows) - n_active} past members")

    req = urllib.request.Request(
        SYNC_URL,
        data=json.dumps({"live": LIVE, "members": rows}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Apps Script answers a POST with a redirect to the result; urllib follows
    # it as a GET, which is what Google expects.
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode(errors="replace")
    try:
        report = json.loads(text)
    except ValueError:
        sys.exit(f"\nERROR: the Apps Script did not answer with JSON:\n\n{text[:500]}\n")
    if not report.get("ok"):
        sys.exit(f"\nERROR from the Apps Script: {report.get('error')}\n")

    verb = "" if LIVE else "WOULD BE "
    for key, title in (("added", "ADDED"), ("movedToPaid", "MOVED TO PAID"),
                       ("movedToEx", "MOVED TO EX")):
        items = report.get(key) or []
        print(f"\n{verb}{title} ({len(items)})")
        for item in items:
            print(f"  {item}")
    if not LIVE:
        print("\nDry run only. Nothing was changed in Gmail.")


if __name__ == "__main__":
    main()
