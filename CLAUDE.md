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

### Links: new tab or same tab (Mike's rule, Sep 2026)
Anything that leaves the site or downloads a file opens in a new tab, so
people don't lose their place: **every** external `http(s)` link and every
document link (`.pdf`, `.docx`, …) gets `target="_blank" rel="noopener"`.
Add both whenever you add such a link.

Everything else deliberately stays in the same tab, confirmed with Mike:
- links to BARNA's own pages, including the nav — a tab per nav click piles
  up tabs and breaks the Back button, and you can't "lose" the site by
  moving around inside it
- `data-ms-modal` triggers (Join, Log In) — these open a Memberstack modal
  over the current page; a new tab breaks signup and login outright
- `mailto:` links — they hand off to the mail app without navigating

`rel="noopener"` matters on its own: without it the opened page can reach
back into the tab that opened it.

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
- Social links (Instagram, Facebook, LinkedIn, Eventbrite) live in the
  shared footer as `.footer-social`, added Aug 2026. Icons are inline
  SVG — no image files, they inherit colour via `currentColor`, so a
  brand-colour change in `css/style.css` carries through. The Eventbrite
  one is a generic ticket glyph, not Eventbrite's real logo mark.
  Tracking parameters (`igsh`, `mibextid`, `viewAsMember`) were stripped
  from the URLs Mike supplied — don't paste them back in.

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

### GOING LIVE: done 31 Aug 2026, and the price ID did NOT need swapping
`prc_annual-barna-membership-3y5t08ng` is the same in Test and Live. This
note previously said the opposite in strong terms — that it was a Test-only
ID that had to be found-and-replaced across 17 places. **That was wrong**,
and acting on it would have broken working signup links.

Verified 31 Aug 2026 two independent ways: read off the Live dashboard, and
read out of `$memberstackDom.getApp()` on the live site, which reported
`mode: "live"` and that exact price ID, £50 GBP, YEARLY, ACTIVE.

The earlier failure that produced the old note (account created, plan never
attached, Stripe never reached) was real, but the diagnosis was not. The
cause was elsewhere — most likely Stripe not being connected in Live, or the
Memberstack account not yet being on a paid plan, since Live Mode needs one.
If that symptom ever comes back, look at the Stripe connection first, not
the price ID.

What actually carries over from Test to Live, all confirmed on the live site:
- the price ID and the plan IDs, unchanged
- both plans (`BARNA Member — Annual`, `BARNA Member — Manual Access`)
- the `barna-members-area` Gated Content group, still linked to both plans
- the `first-name` / `last-name` custom fields
- the Application ID `app_cmrummrg0005e0su88onb4fmk`

What does **not** carry over: members, and the API keys. Those are the only
things that genuinely differ between the two modes.

`scripts/swap_price_id.sh` is kept for the day a price genuinely does change
(a new plan, a price rise). It is not needed for going live.
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

### Memberstack redirects — mind the old `/barna-site/` path
Set in **Plans → Default Settings → Redirects**, not in the code. They are
app-wide; both plans leave their own redirects blank and inherit these.

When the site moved from `barnawebsite.github.io/barna-site/` to the domain
root (31 Aug 2026) all three still pointed at `/barna-site/members.html`, so
the first real signup landed on a GitHub 404 straight after paying. Current
values:

| Redirect | Value |
|---|---|
| On Signup / On Purchase | `/members.html` |
| On Login | `/members.html` |
| On Logout | `/` |

**The same stale host bit the emails too, found 1 Sep 2026.** Memberstack
builds the links in its own transactional email (verify address, password
reset) from the app's configured domain, which was still
`barnawebsite.github.io`. That host 404s: only `/barna-site/` was ever
published there, and it now 301s to `barna.co.uk`, while the bare host has
nothing. So every emailed link was dead. Set the domain to `barna.co.uk` in
the Memberstack dashboard. This matters far more than it looks, because the
legacy-member onboarding depends entirely on password reset links working.

Memberstack also sends a verification email the moment a member is created,
including one created through the Admin API. `CreateMember` has no `verified`
parameter, so the import's PATCH to `verified: true` lands *after* that mail
has already gone. For a bulk onboarding of people who are already known
members, turn email verification off in the dashboard first.

Note `/members` also resolves — GitHub Pages maps it to `members.html` — but
`/account`, `/profile`, `/dashboard` and `/join` all 404, so don't invent
extensionless paths. This is plain static hosting with no routing.

### The member record is created BEFORE payment
Memberstack creates the account first, then hands off to Stripe. So:
- a "new member" notification arrives before any money moves, and a second
  one once the plan attaches. Both are normal.
- anyone who abandons at the Stripe page leaves a member record with **no
  plan**. They get no access, because the `barna-members-area` gate keys off
  the plan and not the account, so this is noise rather than a hole.
- **member count will run above paid count.** "Is a member" does not mean
  "has paid". Worth remembering when migrating the legacy 91.

This halfway state is almost certainly what produced the old (now corrected)
note claiming signup "silently failed" because of the price ID.

### Discount codes live in Stripe, not Memberstack
Memberstack's Plans → Discounts page hands off to Stripe. Create them at
Stripe → **Products → Coupons → + New**.

Two traps, both hit on 31 Aug 2026:
1. **Test mode coupons only work in test mode.** A coupon made on the test
   side is simply "invalid" at a live checkout, with no useful error.
2. **A coupon is not a promo code.** The coupon is the rule; the customer
   types a *promotion code*. Switch on "Use customer-facing promotion codes"
   at the bottom of the coupon form and enter the code there. Putting the
   string in the coupon's Name field does nothing.

Also: Stripe rejects a coupon that lands the price between about £0.01 and
£1. Not an issue at £50, but it would be on a cheaper plan.

Live codes:
- `BARNA-COMP-9F4TQ2` — 100% off, Forever, capped at 5 redemptions and
  expiring 30 Nov 2026. Comp/testing access. **Deliberately capped and
  dated so a leak cannot become permanent — keep those limits on it.**
- A 50% student code was planned (`Once` duration, expiring end of academic
  year) — check Stripe for whether it was actually created.

If the student rate becomes permanent, a separate £25 student *plan* is
cleaner than a code: nothing to leak, and the count is visible.

### Legacy member access + automatic expiry
Memberstack has no built-in expiration date for manually-granted free
plans, so ~91 pre-existing members are being migrated onto a free
**"BARNA Member — Manual Access"** plan instead of paying via Stripe,
each with an exact cutoff date instead of a fresh 12-month term (their
call, not ours — no free extra months). Since Memberstack can't enforce
that date itself, we built it:
- Each such member gets a custom field `accessexpiresat` (format
  `DD/MM/YYYY`) set to their real expiry date. The literal value `never`
  means open-ended access and is skipped by the job — used for the 11 board
  members, who keep access until someone removes them by hand. Anything
  else, including blank, lands in the job's "NEEDS MANUAL CHECK" list and
  is never removed automatically.
- **Four of the 91 had already lapsed by onboarding day.** Mike's call
  (1 Sep 2026): give those a grace year rather than create them and have the
  expiry job strip access the next morning, and let whoever handles
  membership cancel them if they never renew. This is the one deliberate
  exception to "no free extra months" above; those rows are marked CANCEL in
  the import file's `review_note` column.
- Onboarding the legacy members is two scripts, both dry run by default:
  `scripts/prepare_member_import.py` turns a CSV export of Mike's member
  spreadsheet into a flat import file, and `scripts/import_legacy_members.py`
  creates the accounts and attaches the plan. The import matches on email
  against the existing member list, so re-running it repairs rather than
  duplicates. **The member list itself must never be committed** — the repo
  is public; `_member-list/` and `*member*import*.csv` are gitignored.
- `.github/workflows/member-expiry-check.yml` runs
  `scripts/check_member_expiry.py` daily (07:00 UTC + manual
  `workflow_dispatch`). It only ever looks at members on the Manual
  Access plan — real Stripe-paying members are untouched — and removes
  the plan from anyone whose `accessexpiresat` has passed, which
  correctly re-locks the `barna-members-area` gate for them.
- **Defaults to dry run** (logs what it would do, changes nothing).
  Flip it live by setting the repo variable `EXPIRY_CHECK_LIVE_MODE` to
  `true` (Settings → Secrets and variables → Actions → Variables).
- Needs two things set in that same Settings page before it can run at
  all: secret `MEMBERSTACK_SECRET_KEY` (Admin API key) and variable
  `MANUAL_ACCESS_PLAN_ID` (the plan's `pln_...` ID). Missing config
  fails the job with an explicit message and changes nothing.
- Removal here is a simple plan removal via Admin API — nothing manual,
  no separate "expired members list" to maintain. Whoever handles
  renewals should still check periodically who's expired and send the
  actual renewal email; this job only handles revoking access on time.
- **Verified working end to end in Test Mode (Aug 2026):** a member one
  day past expiry had their plan removed by the scheduled run and lost
  members-area access; a member expiring in 2027 was untouched and kept
  full access. Secrets/variables are configured and LIVE mode is on.

#### Undocumented API call — where it came from
Memberstack's public REST docs cover Data Tables only; plan add/remove
is documented purely as the `@memberstack/admin` npm package. The real
call, read out of that package's source, is
`POST /members/{id}/remove-plan` with `{"planId": ...}`, and it returns
plain `OK`, not JSON. (`DELETE /members/{id}/plans/{connectionId}` is
*not* a real endpoint — it 404s; that mistake cost a failed live run.)
If this ever starts 404ing, re-download the npm tarball and re-read
`lib/methods/members/index.js` rather than guessing.

#### ⚠️ Admin API cannot set a password on an existing member
`CreateMember` accepts `password`; `UpdateMember` does not — a PATCH
with a password returns `200 OK` and silently ignores it. So there is
no admin route to "just set a password" for someone. Consequences:
- Legacy members must set their own password via signup or password
  reset. This was previously written up as a **hard blocker** requiring a
  `barna.co.uk` mailbox first. **That is wrong** — checked 31 Aug 2026:
  Memberstack sends transactional email from its own `no-reply@memberstack.io`
  by default, so password resets work today with no mailbox and no DNS
  records. Confirmed in practice: signup emails arrived fine while the only
  address on the account was a personal hotmail one.
- A custom sender (**Settings → Email Sender Address**) is therefore a
  quality decision, not a prerequisite. It buys mail from `@barna.co.uk`
  and better deliverability. It needs **one MX and two TXT records**, so it
  still waits on DNS control, i.e. the registrar move off SYPO.
  Memberstack uses Resend, which asks for an **MX record** — but on the
  `send.` subdomain, not the apex, so the existing `mx.stackmail.com` MX
  and the apex SPF are both untouched and no SPF merge is needed
  (confirmed 1 Sep 2026). Section 4 of `dns-cutover.md` has the exact
  records and the dig checks that prove mail still works.
- Judgement call for the 91: sending from `memberstack.io` works, but
  Memberstack has a known issue with verification and welcome mail landing
  in spam. For a one-off bulk onboarding of 91 people, set up the custom
  sender first — 91 undelivered password resets becomes 91 support emails.
- For *test* members only, the workaround is delete + recreate with a
  password in the create call, then PATCH `verified: true`.

### ⚠️ GOING LIVE: the expiry job still needs its key swapped
This section also used to say "nothing carries over" and list four things
to recreate. Mostly wrong, same as the price ID note above. Verified on the
live site 31 Aug 2026: **the plans and the Gated Content group carry over
with their IDs intact**, so `MANUAL_ACCESS_PLAN_ID` does not change. The
Manual Access plan is `pln_barna-member-manual-access-xx8x0ihb` in both
modes, and it is already linked to the members area group in Live.

What is still true, and still matters:
1. **Members do not carry over.** Green ✅ runs against test members prove
   nothing about live ones.
2. **API keys are per mode.** Generate a **Live Mode** Admin API key and
   update the `MEMBERSTACK_SECRET_KEY` repo secret. This is the one item
   from the old list that genuinely has to be done.
3. ~~Confirm the **`accessexpiresat`** custom field exists in Live.~~ Done,
   1 Sep 2026: it saves and reads back correctly on a real live member, and
   shows as a column in the dashboard. Note it does *not* appear in
   `getApp().customFields`, which lists only dashboard-defined form fields,
   so its absence there is not evidence of a problem.
4. Run the workflow manually **with `EXPIRY_CHECK_LIVE_MODE` unset or
   `false` first** and read the dry-run log against real members before
   letting it delete anything.

### ⚠️ GitHub disables cron on inactive public repos after 60 days
This repo is public and static, so it can easily sit untouched for
months — at which point GitHub **automatically disables the scheduled
workflow** and expiry silently stops happening. GitHub emails the repo
owner first, but it's easy to miss. Either push something occasionally
or re-enable it from the Actions tab when warned.

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

### Custom domain (not done yet) — see `dns-cutover.md`
`dns-cutover.md` at the repo root is the prepared step-by-step for this:
current DNS snapshot, the exact GitHub Pages records, the Memberstack
sender setup, DMARC, and the order to do them in. Written Aug 2026 while
waiting on domain access, so the cutover is copy-paste rather than
research. **Its "Do not break email" section matters most** — MX and SPF
must survive the move, and there must only ever be one SPF record.


barna.co.uk still points at the old Weebly site. To switch: Settings →
Pages → Custom domain, plus DNS records at the registrar. GitHub issues
free HTTPS. That's the last step before Weebly can be retired.

## Working style
- One task/page at a time, not bulk production.
- Mike prefers direct changes over long explanations first.
- Always flag assumptions rather than guessing silently on anything
  brand- or content-related.
