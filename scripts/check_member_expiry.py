"""
BARNA legacy-access expiry checker.

For members on the free "BARNA Member — Manual Access" plan (used to give
legacy members temporary access without going through Stripe), this checks
each member's `accessexpiresat` custom field (format DD/MM/YYYY) against
today's date and removes the plan from anyone whose date has passed.

Dry run by default: only prints what it would do. Set EXPIRY_CHECK_LIVE_MODE=true
to actually remove access. Real members on a real paid plan are never touched —
this only ever looks at the Manual Access plan.

Required environment variables:
  MEMBERSTACK_SECRET_KEY   - Memberstack Admin API secret key
  MANUAL_ACCESS_PLAN_ID    - the plan ID to check, e.g. pln_barna-member-manual-access-xx8x0ihb

Optional:
  EXPIRY_CHECK_LIVE_MODE   - "true" to actually remove expired members' plans (default: dry run)
"""
import os
import sys
import datetime
import urllib.request
import json

def require_env(name, where, example=""):
    value = os.environ.get(name, "").strip()
    if not value:
        hint = f"\n  Example value: {example}" if example else ""
        sys.exit(
            f"\nERROR: {name} is not set, so this job cannot run.\n\n"
            f"  Fix: GitHub repo -> Settings -> Secrets and variables -> Actions\n"
            f"       -> {where} tab -> add '{name}'.{hint}\n\n"
            f"  Nothing was changed in Memberstack.\n"
        )
    return value


API_KEY = require_env("MEMBERSTACK_SECRET_KEY", "Secrets")
PLAN_ID = require_env(
    "MANUAL_ACCESS_PLAN_ID", "Variables", "pln_barna-member-manual-access-xx8x0ihb"
)
LIVE = os.environ.get("EXPIRY_CHECK_LIVE_MODE", "false").strip().lower() == "true"
BASE_URL = "https://admin.memberstack.com"

COMMON_HEADERS = {
    "X-API-KEY": API_KEY,
    "User-Agent": "Mozilla/5.0 (compatible; BARNA-expiry-script/1.0)",
    "Accept": "application/json",
}


def api_get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=COMMON_HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def remove_plan(member_id, plan_id):
    """Remove a free plan from a member.

    Mirrors the official @memberstack/admin package's removeFreePlan():
    POST /members/{id}/remove-plan with {"planId": ...}. This endpoint isn't
    in the public REST docs — it was taken from the npm package's source, so
    check there first if it ever starts 404ing. Returns plain "OK", not JSON.
    """
    body = json.dumps({"planId": plan_id}).encode()
    headers = dict(COMMON_HEADERS, **{"Content-Type": "application/json"})
    req = urllib.request.Request(
        f"{BASE_URL}/members/{member_id}/remove-plan",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode(errors="replace").strip()


def fetch_all_members():
    members = []
    end_param = ""
    while True:
        page = api_get(f"/members?limit=50{end_param}")
        members.extend(page["data"])
        if not page.get("hasNextPage"):
            break
        end_param = f"&after={page['endCursor']}"
    return members


def parse_uk_date(s):
    try:
        day, month, year = s.strip().split("/")
        return datetime.date(int(year), int(month), int(day))
    except Exception:
        return None


def main():
    today = datetime.date.today()
    members = fetch_all_members()

    to_remove = []
    to_keep = []
    to_check = []

    for m in members:
        plan_conn = next(
            (p for p in m.get("planConnections", [])
             if p.get("planId") == PLAN_ID and p.get("status") == "ACTIVE"),
            None,
        )
        if not plan_conn:
            continue

        email = m["auth"]["email"]
        raw_date = m.get("customFields", {}).get("accessexpiresat")
        if not raw_date:
            to_check.append((email, "no accessexpiresat value set"))
            continue

        expiry = parse_uk_date(raw_date)
        if expiry is None:
            to_check.append((email, f"unparseable date '{raw_date}'"))
            continue

        if expiry < today:
            to_remove.append((email, m["id"], plan_conn["id"], expiry))
        else:
            to_keep.append((email, expiry))

    print(f"Today: {today.isoformat()}")
    print(f"Mode: {'LIVE' if LIVE else 'DRY RUN'}")
    print(f"Members on Manual Access plan: {len(to_remove) + len(to_keep) + len(to_check)}")
    print()

    print(f"{'REMOVING' if LIVE else 'WOULD REMOVE'} ({len(to_remove)}):")
    for email, member_id, conn_id, expiry in to_remove:
        print(f"  - {email}  (expired {expiry.isoformat()})")

    print()
    print(f"OK, staying ({len(to_keep)}):")
    for email, expiry in to_keep:
        print(f"  - {email}  (expires {expiry.isoformat()})")

    if to_check:
        print()
        print(f"NEEDS MANUAL CHECK ({len(to_check)}):")
        for email, reason in to_check:
            print(f"  - {email}  ({reason})")

    if not LIVE:
        print()
        print("Dry run only — nothing was changed. Set EXPIRY_CHECK_LIVE_MODE=true to go live.")
        return

    print()
    failures = 0
    for email, member_id, conn_id, expiry in to_remove:
        try:
            remove_plan(member_id, PLAN_ID)
            print(f"  removed: {email}")
        except Exception as e:
            failures += 1
            print(f"  FAILED: {email} -> {e}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
