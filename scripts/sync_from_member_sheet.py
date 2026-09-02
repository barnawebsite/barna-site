"""
Bring Memberstack in line with the membership secretary's own spreadsheet.

She keeps maintaining ACTIVE MEMBERS on the BARNA Google Drive exactly as she
always has. This reads a CSV export of it, works out what differs from the
live member list, and applies the difference. That way a renewal she types
into her sheet actually reaches the website instead of only looking done.

    File -> Download -> Comma Separated Values, then:
    python3 scripts/sync_from_member_sheet.py ~/Downloads/ACTIVE\\ MEMBERS.csv

Dry run by default: it prints the plan and changes nothing. Set
MEMBER_SYNC_LIVE_MODE=true to apply.

What it will do
  - create members who are in her sheet but not on the site
  - update an expiry date she has changed
What it will never do
  - remove anybody. Someone deleted from her sheet is reported and left
    alone: revoking access is the expiry job's job, on a date, or a human's.
  - import a row the parser flagged. An unreadable date, a duplicate or a
    bad email address is written to a review file for a person to settle.
    This is the rule that makes reading a hand-maintained sheet safe.

The parsing is `scripts/prepare_member_import.py` and the writing is
`scripts/import_legacy_members.py`, both called as subprocesses rather than
reimplemented, so there is one tested copy of each. This script only decides
what needs doing.

Required environment variables:
  MEMBERSTACK_SECRET_KEY   - Memberstack Admin API secret key, Live mode
  MANUAL_ACCESS_PLAN_ID    - e.g. pln_barna-member-manual-access-xx8x0ihb

Optional:
  MEMBER_SYNC_LIVE_MODE    - "true" to actually write (default: dry run)
"""
import argparse
import csv
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

BASE_URL = "https://admin.memberstack.com"
FIELD_FIRST = "first-name"
FIELD_LAST = "last-name"
FIELD_EXPIRY = "accessexpiresat"

HERE = os.path.dirname(os.path.abspath(__file__))
PREPARE = os.path.join(HERE, "prepare_member_import.py")
IMPORT = os.path.join(HERE, "import_legacy_members.py")

DEFAULT_REVIEW = "_member-list/needs-review.txt"


def require_env(name, example=""):
    value = os.environ.get(name, "").strip()
    if not value:
        hint = f"\n  Example value: {example}" if example else ""
        sys.exit(f"\nERROR: {name} is not set, so this cannot run.{hint}\n\n"
                 f"  Nothing was changed in Memberstack.\n")
    return value


API_KEY = require_env("MEMBERSTACK_SECRET_KEY")
PLAN_ID = require_env("MANUAL_ACCESS_PLAN_ID",
                      "pln_barna-member-manual-access-xx8x0ihb")
LIVE = os.environ.get("MEMBER_SYNC_LIVE_MODE", "false").strip().lower() == "true"

if API_KEY.startswith("sk_sb_"):
    sys.exit("\nERROR: that is the TEST secret key, not the Live one. The sync\n"
             "  would think every real member is missing and try to create\n"
             "  all of them in the test account.\n")
if not API_KEY.startswith("sk_"):
    sys.exit("\nERROR: MEMBERSTACK_SECRET_KEY should start with 'sk_'.\n")


def api(method, path):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"X-API-KEY": API_KEY,
                 "User-Agent": "Mozilla/5.0 (compatible; BARNA-sync-script/1.0)",
                 "Accept": "application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode(errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace").strip()
        sys.exit(f"\nERROR: {method} {path} -> HTTP {exc.code}\n\n  {detail}\n\n"
                 f"  Nothing was changed in Memberstack.\n")


def fetch_all_members():
    members, end_param = [], ""
    while True:
        page = api("GET", f"/members?limit=50{end_param}")
        members.extend(page["data"])
        if not page.get("hasNextPage"):
            break
        end_param = f"&after={page['endCursor']}"
    return members


def on_manual_access(member):
    return any(p.get("planId") == PLAN_ID and p.get("status") == "ACTIVE"
               for p in member.get("planConnections", []))


# prepare_member_import.py flags rows for two different reasons, and only one
# of them should stop a sync. "Expires soon after onboarding" was a sensible
# thing to pause on when creating 93 accounts in one go; here it would refuse a
# genuine renewal simply because the new date is close, so it is not blocking.
# Anything casting doubt on WHICH date or WHO the person is stays blocking.
BLOCKING_NOTES = (
    "could not read",
    "no expiry date could be set",
    "does not look valid",
    "duplicate of sheet row",
    "ambiguous",
    "read as us month/day",
    # prepare_member_import.py gives anyone already lapsed a grace year, which
    # was Mike's deliberate one-off call for onboarding day so that 93 people
    # were not created and stripped the next morning. Applied silently on every
    # sync it would quietly extend access for someone who has stopped paying,
    # so here it is a decision for a person, not a default.
    "given a grace year",
)


def is_blocking(row):
    """Should this row be kept away from Memberstack until a person decides?"""
    expiry = row["access_expires_at"].strip()
    if not expiry:
        return "no expiry date could be set, needs one by hand"
    if expiry.lower() != "never":
        try:
            day, month, year = expiry.split("/")
            datetime.date(int(year), int(month), int(day))
        except Exception:
            return f"date {expiry!r} is not DD/MM/YYYY"
    note = (row.get("review_note") or "").lower()
    for phrase in BLOCKING_NOTES:
        if phrase in note:
            return row["review_note"]
    return None


def run_prepare(source, out_csv, held_txt):
    """Turn her sheet into the flat import format, using the existing script."""
    result = subprocess.run(
        [sys.executable, PREPARE, source, "--out", out_csv, "--held", held_txt,
         "--include-flagged"],
        capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"\nERROR: could not read the sheet export.\n\n"
                 f"{result.stdout}{result.stderr}\n"
                 f"  Nothing was changed in Memberstack.\n")
    return result.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="CSV export of the ACTIVE MEMBERS sheet")
    ap.add_argument("--review", default=DEFAULT_REVIEW,
                    help=f"where to write the rows a person must settle "
                         f"(default: {DEFAULT_REVIEW})")
    ap.add_argument("--log", default="_member-list/sync-log.csv",
                    help="where the import step writes its per-member result")
    args = ap.parse_args()

    today = datetime.date.today()
    workdir = tempfile.mkdtemp(prefix="barna-sync-")
    prepared_csv = os.path.join(workdir, "prepared.csv")
    prepare_out = run_prepare(args.source, prepared_csv,
                              os.path.join(workdir, "held.txt"))

    with open(prepared_csv, newline="", encoding="utf-8-sig") as fh:
        prepared = list(csv.DictReader(fh))

    live_members = {m["auth"]["email"].strip().lower(): m
                    for m in fetch_all_members() if on_manual_access(m)}

    to_create, to_update, unchanged, flagged = [], [], [], []
    seen = set()

    for row in prepared:
        email = row["email"].strip()
        key = email.lower()
        seen.add(key)

        blocker = is_blocking(row)
        if blocker:
            flagged.append((row, blocker))
            continue

        member = live_members.get(key)
        if member is None:
            to_create.append(row)
            continue

        current = ((member.get("customFields") or {}).get(FIELD_EXPIRY) or "").strip()
        wanted = row["access_expires_at"].strip()
        if current != wanted:
            to_update.append((row, current or "(blank)", wanted))
        else:
            unchanged.append(row)

    # prepare flags only the second copy of a duplicated email. If the two rows
    # disagree about the date, acting on whichever came first is a guess, so
    # hold back every row involved.
    duplicated = set()
    for row, why in flagged:
        for match in re.finditer(r"duplicate of sheet row (\d+)", why or ""):
            duplicated.add(f"sheet-row-{match.group(1)}")
    if duplicated:
        for bucket in (to_create, to_update):
            for item in list(bucket):
                row = item[0] if isinstance(item, tuple) else item
                if row["legacy_id"] in duplicated:
                    bucket.remove(item)
                    flagged.append((row, "another row in the sheet has this "
                                         "same email address"))

    gone = [m for key, m in live_members.items() if key not in seen]

    print(f"Today: {today.isoformat()}")
    print(f"Mode: {'LIVE' if LIVE else 'DRY RUN'}")
    print(f"Sheet: {args.source}")
    print(f"Rows read from the sheet: {len(prepared)}")
    print(f"Members currently on the site: {len(live_members)}")
    print()

    print(f"WOULD CREATE ({len(to_create)}):" if not LIVE
          else f"CREATING ({len(to_create)}):")
    for row in to_create:
        print(f"  - {row['email']}  ({row['first_name']} {row['last_name']}, "
              f"expires {row['access_expires_at']})")

    print()
    print(f"{'WOULD UPDATE' if not LIVE else 'UPDATING'} DATE ({len(to_update)}):")
    for row, current, wanted in to_update:
        print(f"  - {row['email']}  {current} -> {wanted}")

    print()
    print(f"Unchanged ({len(unchanged)})")

    noted = [r for r in to_create + [u[0] for u in to_update]
             if (r.get("review_note") or "").strip()]
    if noted:
        print()
        print(f"Applied, but the parser made an assumption ({len(noted)}):")
        for row in noted:
            print(f"  - {row['email']}  ({row['review_note']})")

    if gone:
        print()
        print(f"⚠️  ON THE SITE BUT NOT IN THE SHEET ({len(gone)}), left alone:")
        for m in gone[:10]:
            expiry = ((m.get("customFields") or {}).get(FIELD_EXPIRY) or "?")
            print(f"  - {m['auth']['email']}  (expires {expiry})")
        if len(gone) > 10:
            print(f"  ... and {len(gone) - 10} more. A number this large "
                  f"usually means the export is partial, not that people left.")
        print("  Nobody is ever removed automatically. If one of these has")
        print("  genuinely left, remove them in Memberstack by hand.")

    if flagged:
        print()
        print(f"HELD BACK FOR A PERSON TO SETTLE ({len(flagged)}), not imported:")
        for row, why in flagged:
            print(f"  - {row['email']}  ({why})")
        review_dir = os.path.dirname(args.review)
        if review_dir:
            os.makedirs(review_dir, exist_ok=True)
        with open(args.review, "w", encoding="utf-8") as fh:
            fh.write("Rows in the member sheet that need a human decision\n")
            fh.write(f"Written {today.isoformat()} by "
                     f"scripts/sync_from_member_sheet.py\n")
            fh.write("None of these were created or changed in Memberstack.\n\n")
            for row, why in flagged:
                fh.write(f"{row['first_name']} {row['last_name']}\n")
                fh.write(f"    email    {row['email']}\n")
                fh.write(f"    date     {row['access_expires_at'] or '(none)'}\n")
                fh.write(f"    {row['legacy_id']}\n")
                fh.write(f"    why      {why}\n\n")
        print(f"  Written to {args.review}")

    if not to_create and not to_update:
        print()
        print("Nothing to do: the site already matches the sheet.")
        return

    if not LIVE:
        print()
        print("Dry run only — nothing was changed. "
              "Set MEMBER_SYNC_LIVE_MODE=true to apply.")
        return

    # Hand the actual writing to the import script, which already creates,
    # attaches the plan, pre-verifies and reads the fields back to prove they
    # saved. --only keeps it to exactly the rows decided above.
    acting = [r["email"] for r in to_create] + [r[0]["email"] for r in to_update]
    apply_csv = os.path.join(workdir, "apply.csv")
    with open(apply_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(prepared[0].keys()))
        writer.writeheader()
        writer.writerows([r for r in to_create] + [r[0] for r in to_update])

    print()
    print("Applying via scripts/import_legacy_members.py ...")
    env = dict(os.environ, MEMBER_IMPORT_LIVE_MODE="true")
    result = subprocess.run(
        [sys.executable, IMPORT, apply_csv, "--only", ",".join(acting),
         "--log", args.log],
        env=env, text=True)
    if result.returncode != 0:
        sys.exit("\nERROR: the import step failed. Read its output above; the "
                 "sync made no other changes.\n")


if __name__ == "__main__":
    main()
