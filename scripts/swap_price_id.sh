#!/usr/bin/env bash
#
# Swap the Memberstack price ID across every page.
#
# The signup links carry a Test Mode price ID until BARNA goes live. That ID
# does not exist in Live Mode: signup then creates the account, silently fails
# to attach the plan, never reaches Stripe, and leaves the member locked out of
# the gated area with no error shown. See CLAUDE.md, "GOING LIVE".
#
# Usage:
#   scripts/swap_price_id.sh prc_the-new-live-id
#
# Get the new ID from Memberstack (switched to Live Mode) -> Plans -> the
# GBP 50/year plan. Run from the repo root. Review with `git diff`, then commit
# and push.

set -euo pipefail

OLD_ID="prc_annual-barna-membership-3y5t08ng"
NEW_ID="${1:-}"

if [[ -z "$NEW_ID" ]]; then
  echo "error: no new price ID given" >&2
  echo "usage: scripts/swap_price_id.sh prc_the-new-live-id" >&2
  exit 1
fi

if [[ ! "$NEW_ID" =~ ^prc_[A-Za-z0-9_-]+$ ]]; then
  echo "error: '$NEW_ID' does not look like a Memberstack price ID (expected prc_...)" >&2
  exit 1
fi

if [[ "$NEW_ID" == "$OLD_ID" ]]; then
  echo "error: that is the Test Mode ID already in the pages, not a Live one" >&2
  exit 1
fi

if [[ ! -f index.html ]]; then
  echo "error: run this from the repo root" >&2
  exit 1
fi

before=$(grep -ro "$OLD_ID" --include='*.html' . | wc -l | tr -d ' ')
if [[ "$before" == "0" ]]; then
  echo "Nothing to do: the Test Mode ID is not present. Already swapped?"
  exit 0
fi

echo "Replacing $before occurrence(s) of the Test Mode ID."

# macOS and GNU sed disagree about -i, so write through a temp file instead.
while IFS= read -r f; do
  tmp="${f}.swaptmp"
  sed "s|${OLD_ID}|${NEW_ID}|g" "$f" > "$tmp"
  mv "$tmp" "$f"
  echo "  updated $f"
done < <(grep -rl "$OLD_ID" --include='*.html' .)

after=$(grep -ro "$OLD_ID" --include='*.html' . | wc -l | tr -d ' ')
now=$(grep -ro "$NEW_ID" --include='*.html' . | wc -l | tr -d ' ')

echo
echo "Test Mode ID remaining: $after (expected 0)"
echo "New ID now present:     $now (expected $before)"

if [[ "$after" != "0" || "$now" != "$before" ]]; then
  echo "MISMATCH. Do not commit. Run 'git checkout -- .' and investigate." >&2
  exit 1
fi

echo
echo "Done. Now:"
echo "  git diff            # check it looks right"
echo "  git commit -am 'Swap Memberstack price ID to Live Mode'"
echo "  git push origin main"
echo "  then test one real signup end to end before announcing it"
