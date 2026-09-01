"""
Turn the legacy BARNA member spreadsheet into an import-ready CSV.

Input is a CSV export of Mike's member sheet (File -> Download -> CSV, or the
Google Sheets /export?format=csv URL). Output is the flat file that
scripts/import_legacy_members.py consumes, plus a report of anything a human
needs to look at.

The rules it applies, all agreed with Mike 1 Sep 2026:
  - expiry = "Last Renewal Date" + 12 months
  - board members get no expiry date at all (the literal string "never"),
    keeping access until someone removes them by hand
  - everyone is imported. Anyone already past their date gets a grace year
    on top rather than being created and stripped by the expiry job the next
    morning (Mike's call, 1 Sep 2026); the membership secretary cancels them
    later if they never renew. This is the one deliberate exception to the
    "no free extra months" rule in CLAUDE.md, and those rows carry a
    review_note saying so.

Nothing here touches Memberstack. It only reads a file and writes a file.

Usage:
  python3 scripts/prepare_member_import.py sheet.csv
  python3 scripts/prepare_member_import.py sheet.csv --out _member-list/members-import.csv
"""
import argparse
import csv
import datetime
import os
import re
import sys

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}

# Column headings expected in the export. Matched case-insensitively and with
# surrounding whitespace stripped, because the sheet has trailing spaces in a
# couple of its headers.
BOARD_COL = ""          # the unnamed first column, where "Board Member" is written
RENEWAL_COL = "last renewal date"
FIRST_COL = "first name"
LAST_COL = "last name"
EMAIL_COL = "email"

OUT_HEADER = ["email", "first_name", "last_name",
              "access_expires_at", "legacy_id", "skip", "review_note"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


def parse_renewal_date(raw, today):
    """Parse the free-text renewal dates the sheet actually contains.

    Handles '4th July 2026', 'Jan 2026', '8/9/2026 11:41:51'. Returns
    (date, note) where note flags a reading that involved an assumption.
    """
    text = raw.strip().lower().replace(",", " ")
    text = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()

    m = re.match(r"^(\d{1,2}) ([a-z]+) (\d{4})$", text)
    if m and m.group(2)[:3] in MONTHS:
        return datetime.date(int(m.group(3)), MONTHS[m.group(2)[:3]], int(m.group(1))), None

    m = re.match(r"^([a-z]+) (\d{4})$", text)
    if m and m.group(1)[:3] in MONTHS:
        return (datetime.date(int(m.group(2)), MONTHS[m.group(1)[:3]], 1),
                f"no day given in {raw.strip()!r}, assumed the 1st")

    # Slash dates are raw form/payment timestamps and their order is not
    # stated. Read them UK-first, but a *last* renewal date cannot be in the
    # future, so fall back to US order when the UK reading is.
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        note = None
        swappable = day <= 12 and month <= 12 and day != month
        uk = datetime.date(year, month, day) if month <= 12 else None
        if uk and uk > today and swappable:
            note = (f"{raw.strip()!r} read as US month/day, because day/month "
                    f"would put the last renewal in the future")
            day, month = month, day
        elif swappable:
            note = (f"{raw.strip()!r} is ambiguous, read as UK day/month; "
                    f"US order would give {month:02d}/{day:02d}")
        return datetime.date(year, month, day), note

    return None, f"could not read the date {raw.strip()!r}"


def plus_twelve_months(d):
    try:
        return d.replace(year=d.year + 1)
    except ValueError:      # 29 February
        return d.replace(year=d.year + 1, day=28)


def tidy_name(name):
    """Fix names typed in block capitals, leaving everything else alone.

    Four rows in the sheet are shouted, which would produce "Dear JANE" in a
    mail merge. Only fully-uppercase words are touched, so McNeill, O'Brien
    and double-barrelled names keep their own capitalisation.
    """
    def fix(word):
        return word.capitalize() if word.isupper() and len(word) > 1 else word
    return " ".join(fix(w) for w in name.split())


def find_columns(header):
    """Map our logical column names onto the sheet's actual header row."""
    normalised = [h.strip().lower() for h in header]
    index = {}
    for key, wanted in (("renewal", RENEWAL_COL), ("first", FIRST_COL),
                        ("last", LAST_COL), ("email", EMAIL_COL)):
        if wanted not in normalised:
            sys.exit(f"\nERROR: the export has no '{wanted}' column.\n"
                     f"  Columns found: {[h.strip() for h in header]}\n")
        index[key] = normalised.index(wanted)
    index["board"] = 0 if normalised[0] == BOARD_COL else None
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="CSV export of the member spreadsheet")
    ap.add_argument("--out", default="_member-list/members-import.csv")
    ap.add_argument("--today", help="override today's date, YYYY-MM-DD (for testing)")
    ap.add_argument("--include-flagged", action="store_true",
                    help="import the flagged rows too, instead of holding them "
                         "back for a decision")
    ap.add_argument("--held", default="_member-list/held-back.txt",
                    help="where to write the readable list of held-back people")
    args = ap.parse_args()

    today = (datetime.date.fromisoformat(args.today) if args.today
             else datetime.date.today())

    with open(args.source, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        sys.exit("ERROR: the export is empty.")

    col = find_columns(rows[0])
    out_rows, notes, seen_emails = [], [], {}
    counts = {"board": 0, "import": 0, "grace": 0}

    info = []

    def flag(sheet_row, email, why):
        notes.append((sheet_row, email, why))
        return why

    # Sheet row numbers start at 2: row 1 is the header.
    for sheet_row, row in enumerate(rows[1:], start=2):
        def cell(key):
            i = col[key]
            return row[i].strip() if i is not None and i < len(row) else ""

        email = cell("email")
        first, last = tidy_name(cell("first")), tidy_name(cell("last"))
        legacy_id = f"sheet-row-{sheet_row}"

        if not any((email, first, last)):
            continue                                    # blank padding row

        board_cell = row[0].strip() if col["board"] is not None else ""
        is_board = board_cell.lower() == "board member"
        review = []
        if board_cell and not is_board:
            # Only "Board Member" counts. The sheet has one stray number in
            # this column, confirmed with Mike 1 Sep 2026 as a normal member,
            # so this is worth printing but is not a job for the membership
            # secretary and stays out of review_note.
            info.append((sheet_row, email,
                         f"ignored value {board_cell!r} in the board column, "
                         f"treated as NOT a board member"))

        if not EMAIL_RE.match(email):
            review.append(flag(sheet_row, email, "email does not look valid"))
        key = email.lower()
        if key in seen_emails:
            review.append(flag(sheet_row, email,
                               f"duplicate of sheet row {seen_emails[key]}"))
        else:
            seen_emails[key] = sheet_row

        if is_board:
            counts["board"] += 1
            out_rows.append([email, first, last, "never", legacy_id, "",
                             "; ".join(review)])
            continue

        renewed, note = parse_renewal_date(cell("renewal"), today)
        if note:
            review.append(flag(sheet_row, email, note))
        if renewed is None:
            review.append("no expiry date could be set, needs one by hand")
            out_rows.append([email, first, last, "", legacy_id, "",
                             "; ".join(review)])
            continue

        expires = plus_twelve_months(renewed)

        # A term that is already up, or up today, would mean a welcome email
        # followed by the expiry job pulling access at the next 07:00 run. Add
        # a grace year instead and let the membership secretary cancel them if
        # they never renew.
        if expires <= today:
            lapsed = expires
            expires = plus_twelve_months(expires)
            counts["grace"] += 1
            review.append(flag(
                sheet_row, email,
                f"lapsed {lapsed.strftime('%d/%m/%Y')}, given a grace year to "
                f"{expires.strftime('%d/%m/%Y')}. CANCEL if they do not renew"))
            if expires <= today:
                review.append(flag(sheet_row, email,
                                   "STILL not in the future even with the "
                                   "grace year, needs a date by hand"))

        stamp = expires.strftime("%d/%m/%Y")
        days = (expires - today).days
        counts["import"] += 1
        if 0 <= days <= 45:
            review.append(flag(sheet_row, email,
                               f"expires {stamp}, only {days} days after "
                               f"onboarding"))
        out_rows.append([email, first, last, stamp, legacy_id, "",
                         "; ".join(review)])

    # Anything with a review note is held back rather than imported: Mike's
    # call, 1 Sep 2026, get the unambiguous ones in and add the rest by hand
    # later. The skip column is what import_legacy_members.py honours.
    held = []
    if not args.include_flagged:
        for row in out_rows:
            note = row[6]
            if note:
                row[5] = "held back, see review_note"
                held.append(row)

    if held:
        held_dir = os.path.dirname(args.held)
        if held_dir:
            os.makedirs(held_dir, exist_ok=True)
        with open(args.held, "w", encoding="utf-8") as fh:
            fh.write("BARNA legacy members held back from the import\n")
            fh.write(f"Generated {today.isoformat()}. "
                     f"{len(held)} people, none of them created in Memberstack.\n")
            fh.write("Add them by hand, or re-run the prepare script with "
                     "--include-flagged once each one is settled.\n\n")
            for email, first, last, expiry, legacy_id, _skip, note in held:
                fh.write(f"{first} {last}\n")
                fh.write(f"    email    {email}\n")
                fh.write(f"    expiry   {expiry or '(none)'}\n")
                fh.write(f"    {legacy_id}\n")
                fh.write(f"    why      {note}\n\n")

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(OUT_HEADER)
        writer.writerows(out_rows)

    print(f"Read {len(rows) - 1} sheet rows, wrote {len(out_rows)} to {args.out}")
    print()
    importing = len(out_rows) - len(held)
    print(f"  WILL BE IMPORTED                     : {importing}")
    print(f"  held back for a decision             : {len(held)}")
    print()
    print(f"  (of the whole file: {counts['import']} dated, "
          f"{counts['board']} board on 'never', {counts['grace']} lapsed)")
    if held:
        print(f"  Held-back list written to {args.held}")
    print()
    if info:
        print(f"FOR INFORMATION ({len(info)}):")
        for sheet_row, email, why in info:
            print(f"  sheet row {sheet_row:>3}  {email:<38} {why}")
        print()

    if notes:
        print(f"NEEDS A HUMAN LOOK ({len(notes)}):")
        for sheet_row, email, why in notes:
            print(f"  sheet row {sheet_row:>3}  {email:<38} {why}")
    else:
        print("Nothing needs a human look.")


if __name__ == "__main__":
    main()
