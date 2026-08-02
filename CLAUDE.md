# BARNA website — project notes for Claude

This is the new barna.co.uk site: plain static HTML/CSS (no build step, no
framework), served straight from GitHub Pages. It's replacing an
existing Weebly site. Mike (the person you're working with) is a nurse, not a
developer, but is comfortable pasting/editing HTML directly.

## Brand identity — always use these, don't invent alternatives
- Navy `#0D2137` (background/header/footer)
- Teal `#3AABB2` (primary accent)
- Coral `#E8705C` (secondary accent / CTAs)
- Off-white `#D4E8EA` (light text on navy)
- Font: Calibri throughout (`Calibri, "Trebuchet MS", Arial, sans-serif`)
- Logo: use `images/barna-logo.png` exactly as provided — never redraw,
  never reprocess/recolor it. If it ever looks wrong (dark box behind it,
  not blending into the header), the file has been corrupted somewhere —
  ask Mike to re-upload the original rather than trying to fix it yourself.

## Structure
- One shared stylesheet: `css/style.css` — edit here, not per-page, so
  every page updates together.
- Every page repeats the same `<header>` and `<footer>` blocks marked with
  `<!-- ============ SHARED HEADER ============ -->` / SHARED FOOTER
  comments. When the nav or footer changes, it needs updating on every
  page (no server-side includes — this is plain static hosting).
- `<!-- EDIT: ... -->` HTML comments mark placeholder content (fake links,
  TBD copy) that still needs a real value — search for these before
  considering a page "done."

## Navigation (deliberately kept short)
Home · About · Affiliations & Partners · Education & Clinical Practice ·
Paediatric Care · Members Area

Notes on why it's structured this way:
- "Join" is NOT in the nav — it's a hero button + footer link only.
- "Events" is NOT a separate page — event/webinar content lives directly
  on the homepage in the "Events & Webinars" section, since that's the
  content Mike updates most often and he wants only one place to touch.
- "Corporate"/exhibiting is NOT a separate page either — folded into a
  footer link (mailto to adela@barna.co.uk) since it rarely changes.
- Paediatric Care is deliberately its own dedicated nav item — Mike asked
  for this specifically, it's a real focus area, not a subsection.
- ABC Packs pages are NOT in the nav — reached via the Members Area
  "Member Resources" cards only (they're gated member content).

## Current page status
- `index.html`, `about.html`, `affiliations.html`, `education-clinical.html`,
  `members.html` — real content, built out.
- `abc-packs.html` + `airway-grid.html` / `breathing-grid.html` /
  `circulation-grid.html` — gated ABC learning-resource pages, built
  Aug 2026 from the old site's Members Only Area. Small files served
  locally from `assets/documents/abc-packs/`; 15 large presentations and
  workbooks (10–160MB, too big for GitHub) link out to Google Drive
  ("Anyone with the link" sharing, on Mike's Drive account). Local copies
  of those large files sit in `_to-upload-google-drive/` (gitignored) as
  backup.
- `paediatric.html` — has the gated workbook download (`#workbook`
  anchor) plus placeholder public copy. General specialty content is
  still the biggest remaining gap; blocked on Mike sourcing it — don't
  build until he provides it.
- `members.html` — fully built: Member Resources cards (ABC Packs,
  Paediatric workbook), Eventbrite promo, webinar archive with
  recordings/files linked, legacy "Earlier resources" list. The
  `<!-- EDIT: add recording/slides link -->` comments on recent webinar
  cards are intentional slots for future recordings, not gaps.
- `join.html` was removed — Join is a modal (`data-ms-modal="signup"`)
  triggered from the hero button and footer link, not a standalone page.
- The old Weebly site is no longer referenced anywhere — all assets
  migrated (verified Aug 2026); it can be retired without breaking links.
- BARNA Standards of Practice: checked Aug 2026, the 2012 edition is
  current — no newer version exists despite the old site's "updated
  soon" note.

## Membership (Memberstack)
- **Paid-only by design.** Two halves that must stay in sync — if you add
  a gated page, do both or the gate leaks:
  1. Gated blocks use `data-ms-content="barna-members-area"` /
     `"!barna-members-area"` — the key of the "BARNA - Members area"
     Gated Content group in the Memberstack dashboard, which both
     `BARNA Member — Annual` (paid) and `BARNA Member — Manual Access`
     (free, used for legacy-member migration) are linked to. **Do not use
     the reserved keyword `"paid-plans"`** — confirmed with Memberstack
     support (Aug 2026) that it specifically means "has an active
     Stripe-connected paid/subscription plan," so it silently excludes
     any FREE-type plan (like Manual Access) even though the member has
     active, legitimate access. If a new plan is ever added and it should
     also unlock this content, link it to the "BARNA - Members area"
     group in the dashboard, not just to the gate in code. Never
     `"members"` either — that only means "logged in", so a free account
     would see everything.
  2. Every signup link carries
     `data-ms-price:add="prc_annual-barna-membership-3y5t08ng"`, so there
     is no route to an account that skips Stripe. This includes the
     footer "Join BARNA" link, which is repeated on every page.

### ⚠️ GOING LIVE: the price ID must be swapped
`prc_annual-barna-membership-3y5t08ng` is a **Test Mode** price ID. It does
not exist in Live Mode. Confirmed the hard way (Aug 2026): with Memberstack
switched to Live, signup created the account, silently failed to attach the
plan, and never reached Stripe — so the member paid nothing AND stayed locked
out by the `barna-members-area` gate, with no error shown. It looks like a broken site.

When BARNA goes live for real:
1. Switch Memberstack to Live Mode.
2. Copy the **Live** price ID from Plans → the £50/year plan.
3. Find-and-replace the old ID across all `.html` files (17 occurrences,
   10 files — one `sed`/replace, don't hand-edit).
4. Commit and push (GitHub Pages publishes automatically).
5. Test one real signup end to end before announcing it.
- Memberstack script tag is on all pages. Signup is a modal
  (`data-ms-modal="signup"`), never a standalone page.
- Google/social sign-in was switched off in the Memberstack dashboard
  (Aug 2026) — Mike wants name, surname and email from every member.
  Collecting name/surname was still open at the end of that session: the
  pre-built modal may not capture it, in which case the fix is a custom
  form (`data-ms-form="signup"` + `data-ms-member="first-name"` etc.)
  inside the "Not a member yet?" block on members.html.
- Mike is flipping Memberstack from Test Mode to live himself.
- Stripe is connected using Mike's personal details for now — his call
  (Aug 2026): he'll move money manually and swap in BARNA's real
  business/bank details later. Don't treat this as a launch blocker.

## Deploying — GitHub Pages
- **Live site: https://barnawebsite.github.io/barna-site/**
- `git push origin main` is the whole deploy. GitHub's "pages build and
  deployment" workflow publishes in ~1 minute. No dashboards, no buttons,
  no credits — the free tier allows ~10 builds/hour, so push freely.
- Served from branch `main`, folder `/ (root)`. `.nojekyll` at the repo
  root stops Jekyll rewriting anything; leave it there.
- Every link in the site is **relative** — that's what lets it work from
  the `/barna-site/` subpath. Never introduce `href="/..."` absolute
  paths or they'll break until a custom domain is set.
- Moved off Netlify Aug 2026: free tier gave 300 credits/month at 15 per
  deploy (~20 deploys), and Mike ran out. GitHub Pages is free and
  effectively unlimited for a static site. Netlify kept briefly as a
  fallback, then deleted — don't reinstate it.

### If a change doesn't appear on the live site
Check the **output**, not the settings — this bit us three times in one
day. Config that looks correct can still mean nothing ever ran:
- Actions tab → is there a recent green "pages build and deployment"?
- `curl -s https://api.github.com/repos/barnawebsite/barna-site/actions/runs?per_page=3`
- Pages builds fire **on push only**. When Pages was first enabled, no
  build existed until a fresh commit was pushed (an empty commit is a
  fine way to force one: `git commit --allow-empty`).

### Custom domain (not done yet)
barna.co.uk still points at the old Weebly site. To switch: Settings →
Pages → Custom domain, plus DNS records at the registrar. GitHub issues
free HTTPS. That's the last step before Weebly can be retired.

## Working style
- One task/page at a time, not bulk production.
- Mike prefers direct changes over long explanations first.
- Always flag assumptions rather than guessing silently on anything
  brand- or content-related.
