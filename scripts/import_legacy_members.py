"""
BARNA legacy-member onboarding.

Creates Memberstack accounts for the ~91 pre-existing members, puts each one
on the free "BARNA Member — Manual Access" plan, and stamps their
`accessexpiresat` custom field so scripts/check_member_expiry.py can revoke
access on the right day.

Input is the CSV produced by scripts/prepare_member_import.py:
    email,first_name,last_name,access_expires_at,legacy_id,skip,review_note

Dry run by default: prints exactly what it would do and changes nothing. Set
MEMBER_IMPORT_LIVE_MODE=true to actually write to Memberstack.

Safe to run more than once. It reads the existing member list first and
matches on email, so a second run repairs whatever the first one missed
rather than creating duplicates.

⚠️ The Admin API cannot set a password on a member that already exists
(UpdateMember accepts one and silently ignores it). Members created here get
a random password that is never recorded anywhere, so every one of them has
to set their own through "Forgot password" on the members area.

Required environment variables:
  MEMBERSTACK_SECRET_KEY   - Memberstack Admin API secret key, Live mode
  MANUAL_ACCESS_PLAN_ID    - e.g. pln_barna-member-manual-access-xx8x0ihb

Optional:
  MEMBER_IMPORT_LIVE_MODE  - "true" to actually write (default: dry run)

Usage:
  python3 scripts/import_legacy_members.py _member-list/members-import.csv
  python3 scripts/import_legacy_members.py _member-list/members-import.csv --limit 5
"""
import argparse
import csv
import datetime
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "https://admin.memberstack.com"

# Custom field keys as they exist in Memberstack. first-name/last-name were
# confirmed present in Live 31 Aug 2026; accessexpiresat is the one the
# expiry job reads.
FIELD_FIRST = "first-name"
FIELD_LAST = "last-name"
FIELD_EXPIRY = "accessexpiresat"


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


def key_shape(key):
    """Describe the key without revealing it: prefix and length only.

    Memberstack shows three similar-looking values on adjacent screens and
    they are easy to mix up, so this says which one was supplied without
    printing anything usable.
    """
    prefix = key.split("_")[0] + "_" if "_" in key else key[:3]
    return f"starts with {prefix!r} and is {len(key)} characters long"


# Catch the three easy mix-ups before spending a network call on them.
_WRONG_KEY = {
    "paste": "still the placeholder text from the instructions, not a real key",
    "app_": "the Application ID. That one is public and is already in the HTML "
            "of every page on the site. It cannot authenticate anything",
    "pk_": "the PUBLIC key. That is the one that goes in the website's script "
           "tag. It cannot be used to read or change members",
}
for marker, what in _WRONG_KEY.items():
    if API_KEY.lower().startswith(marker) or marker == "paste" and "paste" in API_KEY.lower():
        sys.exit(
            f"\nERROR: that is {what}.\n\n"
            f"  The key supplied {key_shape(API_KEY)}.\n\n"
            f"  You want the SECRET key, which starts with 'sk_':\n"
            f"    Memberstack -> Settings -> API keys -> Secret key,\n"
            f"    with the Test/Live toggle set to LIVE.\n\n"
            f"  Nothing was changed in Memberstack.\n"
        )

if API_KEY.startswith("sk_sb_"):
    sys.exit(
        "\nERROR: that is the TEST secret key, not the Live one.\n\n"
        "  The 'sb' after 'sk_' means sandbox. Test and Live are separate\n"
        "  Memberstack environments with separate keys and separate members,\n"
        "  and a Test key cannot see or change any live member.\n\n"
        "  Flip the Test/Live toggle in the dashboard to LIVE, then take the\n"
        "  Secret key from Settings -> API keys. It will not have 'sb' in it.\n\n"
        "  Nothing was changed in Memberstack.\n"
    )

if not API_KEY.startswith("sk_"):
    sys.exit(
        f"\nERROR: that does not look like a Memberstack secret key.\n\n"
        f"  The key supplied {key_shape(API_KEY)}, but a secret key\n"
        f"  starts with 'sk_'.\n\n"
        f"  Memberstack -> Settings -> API keys -> Secret key, with the\n"
        f"  Test/Live toggle set to LIVE.\n\n"
        f"  Nothing was changed in Memberstack.\n"
    )
PLAN_ID = require_env(
    "MANUAL_ACCESS_PLAN_ID", "Variables", "pln_barna-member-manual-access-xx8x0ihb"
)
LIVE = os.environ.get("MEMBER_IMPORT_LIVE_MODE", "false").strip().lower() == "true"

COMMON_HEADERS = {
    "X-API-KEY": API_KEY,
    "User-Agent": "Mozilla/5.0 (compatible; BARNA-import-script/1.0)",
    "Accept": "application/json",
}


def api(method, path, payload=None):
    headers = dict(COMMON_HEADERS)
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode(errors="replace").strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace").strip()
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from None
    try:
        return json.loads(raw)
    except ValueError:
        return raw          # add-plan / remove-plan return plain "OK"


def fetch_all_members():
    """Every existing member, so the run is idempotent and matches on email."""
    members, end_param = [], ""
    # The package builds this as `first=`, not `limit=`, but
    # check_member_expiry.py has run in production on `limit=` since Aug 2026.
    # Either way the cursor loop below walks every page, so both are correct.
    while True:
        page = api("GET", f"/members?limit=50{end_param}")
        members.extend(page["data"])
        if not page.get("hasNextPage"):
            break
        end_param = f"&after={page['endCursor']}"
    return members


def create_member(row, password):
    """Create a member already on the Manual Access plan.

    Mirrors createMember() in @memberstack/admin: POST /members, with the
    body being exactly the Params.CreateMember shape
    (email, password, customFields, metaData, plans). Like remove-plan this
    is not in the public REST docs, which only cover Data Tables, so it was
    read out of the package source — verified against v1.6.0,
    lib/methods/members/index.js and lib/types/params.d.ts, 1 Sep 2026.
    Re-read those rather than guessing if it ever starts failing.

    Responses are {"data": {...}}, per SinglePayload in lib/types/payload.d.ts.
    """
    return api("POST", "/members", {
        "email": row["email"],
        "password": password,
        "plans": [{"planId": PLAN_ID}],
        "customFields": custom_fields(row),
        "metaData": {"legacyId": row["legacy_id"], "importedFrom": "legacy-sheet"},
    })


def add_plan(member_id):
    """Attach the free plan to a member who already exists.

    The mirror image of remove-plan in check_member_expiry.py.
    """
    return api("POST", f"/members/{member_id}/add-plan", {"planId": PLAN_ID})


def update_custom_fields(member_id, fields):
    return api("PATCH", f"/members/{member_id}", {"customFields": fields})


def read_back(member_id):
    """Re-read a member straight after creating them.

    The Admin API accepts a password on update and silently ignores it
    (see the module docstring), so "200 OK" is not proof a field landed. If
    the accessexpiresat custom field does not exist in this Memberstack app,
    the create would succeed with the date quietly dropped, and the expiry
    job would then never revoke anyone. Reading one back is the only way to
    know it actually stuck.
    """
    got = api("GET", f"/members/{member_id}")
    return got.get("data", got)


def mark_verified(member_id):
    """Mark the email address as already verified.

    Params.CreateMember has no `verified`, only Params.UpdateMember does, so
    this is a second call after the create. These are existing BARNA members
    whose addresses are known good, and Memberstack has a known problem with
    its verification mail landing in spam. Pre-verifying removes one way for
    the onboarding to fail silently. Use --no-verify to leave it to them.
    """
    return api("PATCH", f"/members/{member_id}", {"verified": True})


def custom_fields(row):
    return {
        FIELD_FIRST: row["first_name"],
        FIELD_LAST: row["last_name"],
        FIELD_EXPIRY: row["access_expires_at"],
    }


def has_active_plan(member):
    return any(p.get("planId") == PLAN_ID and p.get("status") == "ACTIVE"
               for p in member.get("planConnections", []))


def validate(rows):
    """Refuse to start on a file that would produce wrong access."""
    problems = []
    seen = {}
    for n, row in enumerate(rows, start=2):
        email = row["email"].strip()
        if not email or "@" not in email:
            problems.append(f"line {n}: missing or malformed email {email!r}")
        key = email.lower()
        if key in seen:
            problems.append(f"line {n}: duplicate of line {seen[key]} ({email})")
        seen[key] = n
        expiry = row["access_expires_at"].strip()
        if expiry.lower() == "never":
            continue
        try:
            day, month, year = expiry.split("/")
            datetime.date(int(year), int(month), int(day))
        except Exception:
            problems.append(
                f"line {n}: {email} has expiry {expiry!r}, which is neither "
                f"DD/MM/YYYY nor 'never'. It would be treated as no date at all."
            )
    if problems:
        sys.exit("\nERROR: the input file is not safe to import.\n\n  "
                 + "\n  ".join(problems)
                 + "\n\n  Nothing was changed in Memberstack.\n")


FRIENDLY_ERRORS = {
    "validation/invalid-secret-key":
        "Memberstack rejected the API key.\n"
        f"  The key supplied {key_shape(API_KEY)}.\n"
        "  - Check it is the LIVE key, not the Test one. They are separate\n"
        "    keys, and a Test key is rejected outright against live data.\n"
        "  - Check nothing was cut off when copying. Use the copy button in\n"
        "    the dashboard rather than selecting the text by hand.\n"
        "  - If Memberstack has no Live secret key to show you, the account\n"
        "    may not be on a paid plan yet, which Live Mode requires.",
    "validation/plan-not-found":
        "Memberstack does not recognise MANUAL_ACCESS_PLAN_ID.\n"
        "  It should be pln_barna-member-manual-access-xx8x0ihb.",
}


def explain(exc):
    """Turn an API failure into something readable, with no traceback."""
    text = str(exc)
    for code, advice in FRIENDLY_ERRORS.items():
        if code in text:
            return f"{advice}\n\n  Full response: {text}"
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="CSV from prepare_member_import.py")
    ap.add_argument("--limit", type=int,
                    help="only process the first N importable rows (test batch)")
    ap.add_argument("--log", default="_member-list/import-log.csv",
                    help="where to write the per-member result")
    ap.add_argument("--no-verify", action="store_true",
                    help="do not pre-mark new members' email as verified")
    args = ap.parse_args()

    with open(args.source, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    missing = {"email", "first_name", "last_name", "access_expires_at",
               "legacy_id", "skip"} - set(rows[0] if rows else {})
    if missing:
        sys.exit(f"ERROR: {args.source} is missing columns: {sorted(missing)}")

    skipped = [r for r in rows if r["skip"].strip()]
    todo = [r for r in rows if not r["skip"].strip()]
    validate(todo)
    if args.limit:
        todo = todo[:args.limit]

    print(f"Mode: {'LIVE' if LIVE else 'DRY RUN'}")
    print(f"New members pre-verified: {'no' if args.no_verify else 'yes'}")
    print(f"Source: {args.source}")
    print(f"Rows: {len(rows)}, marked skip: {len(skipped)}, to process: {len(todo)}"
          + (f" (limited to {args.limit})" if args.limit else ""))
    print()

    try:
        existing = {m["auth"]["email"].lower(): m for m in fetch_all_members()}
    except Exception as exc:
        sys.exit(f"\nERROR: could not read the member list.\n\n  "
                 f"{explain(exc)}\n\n  Nothing was changed in Memberstack.\n")
    print(f"Members already in Memberstack: {len(existing)}")
    print()

    results, failures, created_ids = [], 0, []
    for row in todo:
        email = row["email"].strip()
        member = existing.get(email.lower())

        if member is None:
            action = "create + plan"
        elif not has_active_plan(member):
            action = "already exists, add plan"
        else:
            action = "already done, refresh fields"

        if not LIVE:
            print(f"  would {action:<28} {email}")
            results.append((email, row["legacy_id"], f"would {action}", ""))
            continue

        try:
            if member is None:
                created = create_member(row, secrets.token_urlsafe(24))
                member_id = created.get("data", created).get("id", "")
                if not args.no_verify and member_id:
                    mark_verified(member_id)
                if member_id:
                    created_ids.append(
                        (member_id, email, row["access_expires_at"]))
            else:
                member_id = member["id"]
                if not has_active_plan(member):
                    add_plan(member_id)
                update_custom_fields(member_id, custom_fields(row))
            print(f"  {action:<28} {email}")
            results.append((email, row["legacy_id"], action, member_id))
            time.sleep(0.3)                     # stay well inside the rate limit
        except Exception as exc:
            failures += 1
            print(f"  FAILED  {email}: {explain(exc)}")
            results.append((email, row["legacy_id"], "FAILED", str(exc)))

    log_dir = os.path.dirname(args.log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    with open(args.log, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["email", "legacy_id", "result", "detail"])
        writer.writerows(results)

    if LIVE and created_ids:
        print()
        print("Checking the custom fields actually saved...")
        sample = created_ids[:5]
        mismatched = []
        for member_id, email, wanted in sample:
            try:
                fields = read_back(member_id).get("customFields") or {}
                actual = fields.get(FIELD_EXPIRY)
                if actual != wanted:
                    mismatched.append((email, wanted, actual))
                else:
                    print(f"  ok  {email}  {FIELD_EXPIRY}={actual}")
            except Exception as exc:
                mismatched.append((email, wanted, f"could not read back: {exc}"))
        if mismatched:
            print()
            print("  *** STOP. The expiry date did not save. ***")
            for email, wanted, actual in mismatched:
                print(f"  {email}: expected {wanted!r}, got {actual!r}")
            print()
            print(f"  The '{FIELD_EXPIRY}' custom field almost certainly does not")
            print( "  exist in this Memberstack app. Add it under Members ->")
            print( "  Custom Fields, then re-run: the import matches on email,")
            print( "  so it will repair these rather than duplicate them.")
            print( "  Until it is fixed, nobody's access will ever expire.")
            sys.exit(1)

    print()
    print(f"Wrote {args.log}")
    if not LIVE:
        print("Dry run only — nothing was changed. "
              "Set MEMBER_IMPORT_LIVE_MODE=true to go live.")
        return
    print(f"Done. {len(results) - failures} succeeded, {failures} failed.")
    print("Every member created here still has to set their own password "
          "through 'Forgot password'.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
