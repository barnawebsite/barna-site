# BARNA website — project notes for Claude

This is the new barna.co.uk site: plain static HTML/CSS (no build step, no
framework), meant to be dragged straight into Netlify. It's replacing an
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
Home · About · Education & Clinical Practice · Paediatric Care · Members

Notes on why it's structured this way:
- "Join" is NOT in the nav — it's a hero button + footer link only.
- "Events" is NOT a separate page — event/webinar content lives directly
  on the homepage in the "Events & Webinars" section, since that's the
  content Mike updates most often and he wants only one place to touch.
- "Corporate"/exhibiting is NOT a separate page either — folded into a
  footer link (mailto to adela@barna.co.uk) since it rarely changes.
- Paediatric Care is deliberately its own dedicated nav item — Mike asked
  for this specifically, it's a real focus area, not a subsection.

## Current page status
- `index.html` — real homepage, built out properly.
- `about.html`, `education-clinical.html`, `paediatric.html`, `members.html`,
  `join.html` — placeholder stub pages only ("content being built next").
  These are the next things to build, one at a time, with Mike's input on
  what goes in each (he's copying source content from the old Weebly site).
- Two PDFs on the homepage still point to the *old* Weebly-hosted URLs
  (working, but temporary) — need migrating into `/files/` here before the
  old site is retired.

## Membership (Memberstack)
- Separate from this static site's build — Memberstack app is already set
  up and tested (signup, manual member add, gated content all confirmed
  working in Test Mode).
- `members.html` will eventually sit behind Memberstack's gating once
  wired in — not done yet, this file is still just a placeholder.
- Stripe is connected but currently using placeholder/personal details —
  needs swapping to BARNA's real business/bank details before real
  payments go live.

## Working style
- One task/page at a time, not bulk production.
- Mike prefers direct changes over long explanations first.
- Always flag assumptions rather than guessing silently on anything
  brand- or content-related.
