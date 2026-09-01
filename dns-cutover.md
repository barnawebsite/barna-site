# barna.co.uk DNS cutover pack

Everything needed to point barna.co.uk at the new site and get member
emails working, prepared in advance so the handover day is copy and paste
rather than research. Written for whoever holds the DNS control panel,
which as of Aug 2026 is being transferred from Web by Numbers / Sypo.

**Read the "Do not break email" section before changing anything.**

---

## 0. DONE: cutover completed 31 Aug 2026

The website move is finished. barna.co.uk serves the new GitHub Pages site
over HTTPS. Kept below for the record and for the parts still outstanding.

| Check | State on 31 Aug 2026 |
|---|---|
| A records | all four GitHub IPs |
| www | CNAME to barnawebsite.github.io, 301s to the apex |
| MX / SPF | untouched, email unaffected |
| HTTPS | Let's Encrypt cert for barna.co.uk issued 13:57 UTC, auto-renews |
| Nominet data quality | validated 31 Aug 2026, registrant corrected to BARNA |

**Registrar move completed 1 Sep 2026.** BARNA now holds every layer:

| Layer | Holder |
|---|---|
| Registrant (legal owner) | BARNA, validated at Nominet 31 Aug 2026 |
| Registrar | 20i Ltd, tag `STACK` (was Web by Numbers, `SYPO`) |
| DNS zone | BARNA's own 20i account |
| Website | GitHub Pages, `barnawebsite/barna-site` |

No third party sits in that chain any more. Nameservers remain
`ns1-4.stackdns.com`, which is correct: those are 20i's own shared
nameservers, used by their direct customers as well as their resellers.

Still outstanding: a mailbox on the domain, the Memberstack custom sender
and its DKIM records, onboarding the legacy members, DMARC, and retiring
the old Weebly site.

---

## 1. What was live before the change (Aug 2026)

Snapshot taken before any changes, so it can be compared or restored.

| Record | Current value | What it does |
|---|---|---|
| Nameservers | `ns1`–`ns4.stackdns.com` | DNS is hosted on Sypo's Stack platform |
| A (apex) | `199.34.228.77` | Points barna.co.uk at the **old Weebly site** |
| A (www) | `199.34.228.77` | Same, for www |
| MX | `10 mx.stackmail.com` | Where email for @barna.co.uk is delivered |
| TXT (SPF) | `v=spf1 include:spf.stackmail.com a mx ~all` | Says who may send email as barna.co.uk |
| DMARC | **none** | Not set up. See section 5 |

No `@barna.co.uk` mailboxes are currently in use (confirmed by Alan
Jewitt, July 2026), so there is no mail to lose, but the MX and SPF
records still matter, see below.

---

## 2. ⚠️ Do not break email

The single biggest risk in this whole job. Two different scenarios:

**Scenario A: DNS stays on Stack / Sypo's nameservers.**
You only change the A records in section 3. Leave MX and SPF exactly as
they are. Lowest risk, recommended if the handover gives a login to the
existing setup.

**Scenario B: nameservers move to a new host (20i, 123-reg, etc).**
Everything starts blank at the new host. You must **recreate MX and SPF
there**, using whatever mail provider you end up on, or email for the
domain silently stops working. Write the current values down first, and
set up the new mailbox before switching nameservers, not after.

**Only ever have ONE SPF (TXT) record for the domain.** A second one
does not add to the first, it breaks both. When Memberstack needs its
own sender permission, you *merge* their `include:` into the existing
record, you do not add a new line. See section 4.

---

## 3. Point the domain at the new site (GitHub Pages)

The new site is served from GitHub Pages at
`https://barnawebsite.github.io/barna-site/`.

**Apex domain — replace the existing A record with these four:**

```
A    @    185.199.108.153
A    @    185.199.109.153
A    @    185.199.110.153
A    @    185.199.111.153
```

**Optional but recommended, IPv6:**

```
AAAA  @   2606:50c0:8000::153
AAAA  @   2606:50c0:8001::153
AAAA  @   2606:50c0:8002::153
AAAA  @   2606:50c0:8003::153
```

**www — replace the existing A record with a CNAME:**

```
CNAME   www   barnawebsite.github.io.
```

### ⚠️ Do the GitHub side FIRST, before the DNS records

This is the step that was missed on the first attempt (Aug 2026) and it
is why the cutover failed. Alan added the DNS records correctly, but
GitHub had never been told that `barna.co.uk` belongs to this repo, so
it had no idea where to route the request and served
**"There isn't a GitHub Pages site here."** The DNS was reverted and the
old Weebly site came back. Nothing was broken, but a day was lost.

The two halves are independent and GitHub's half can be done at any
time, with or without the DNS pointing at it:

- **GitHub half:** a file named `CNAME` in the repo root containing the
  single line `barna.co.uk`. Repo → Settings → Pages → Custom domain →
  enter `barna.co.uk` → Save does exactly this and nothing more, so
  committing the file by hand is equivalent. It is already committed to
  this repo. **Do not delete it**, the site breaks without it.
- **DNS half:** the A and CNAME records above, made at the registrar.

GitHub will show a red "DNS check unsuccessful" warning on the Pages
settings page until the DNS half is done. That is expected and correct.
It saves the setting anyway.

**Side effect while you wait:** once the `CNAME` file exists, GitHub
redirects `https://barnawebsite.github.io/barna-site/` to
`https://barna.co.uk`. So during the gap between the two halves, the
github.io preview link stops showing the new site and lands on the old
Weebly one instead. This is temporary and expected, not a fault. If the
preview link is needed again before the DNS is done, delete the `CNAME`
file, push, and it comes straight back.

Once the DNS has propagated and GitHub shows the domain as verified,
tick **Enforce HTTPS** on the same page. GitHub issues the certificate
free. It can take up to 24 hours to become available, and the tickbox
stays greyed out until then, which is normal.

Note: every link on the site is relative, so nothing in the HTML needs
changing when it moves from the `/barna-site/` subpath to the domain
root.

---

## 4. Make member emails work (Memberstack)

Memberstack will not send from a free domain like gmail. It needs a
sender address on barna.co.uk plus DNS records proving we own it.

### 4a. Create the mailbox first, at 20i

The sender must be a **real mailbox**, not a forwarder — Memberstack will
not let an address be used until it is reachable, and this same address
becomes the 20i account login (section 11). Mail for barna.co.uk already
points at `mx.stackmail.com`, which is 20i's own mail platform, so the
mailbox belongs there and **no MX change is needed to create it**.

#### DONE 1 Sep 2026 — and no hosting package was needed

`info@barna.co.uk` was created this way: Standard mailbox, 10 GB, zero
bytes used. **Confirmed in practice that 20i charges nothing extra and
asks for no package.**

⚠️ **Inbound took about an hour to start working, not the 30 minutes 20i
advertises.** Created 13:35, first successful inbound delivery around
14:30. Sending *out* from webmail worked almost immediately, and logging in
worked immediately, which makes the gap genuinely confusing: every signal
says the mailbox is fine while mail still goes nowhere. Throughout that
window the MX correctly answered `250 Accepted` for the address, so nothing
was being lost, just not yet delivered. If this happens again, wait a full
hour before treating it as a fault or raising a ticket.

#### ⚠️ Do NOT buy a hosting package for this

20i bundles mailboxes with hosting, so the obvious read of their pricing
is that email needs a package. It does not. **20i allows exactly one
mailbox per domain with no hosting at all**, which is precisely what BARNA
needs — `info@` is the only address that has to receive anything. The site
is on GitHub Pages and needs no hosting either.

It is also not merely wasteful: the mailbox screen appears on the domain
**only while no hosting is attached**. Buying a package moves email
management into the package instead, so it changes the route as well as
the bill.

20i control panel → **Manage Domain Names** → `barna.co.uk` → **Options →
Manage** → **Email Accounts** → type `info` → **Create Email Account** →
set a password. Then log into webmail once (`https://webmail.stackmail.com`)
and confirm a test message from an outside address arrives.

If a second mailbox is ever genuinely needed, that is the point at which a
package becomes the honest answer — not before.

#### Creating the mailbox adds four CNAMEs — leave them alone

20i silently wrote these into the zone at the same time. They are mail
client autodiscovery records, not cruft, and they are **not** in the
original zone list further down this document because they did not exist
when it was written:

```
CNAME  imap    imap.stackmail.com.
CNAME  mail    mail.stackmail.com.
CNAME  pop3    pop3.stackmail.com.
CNAME  smtp    smtp.stackmail.com.
```

They are harmless to the website — only the apex A records and `www`
matter to GitHub Pages — and they do not collide with the `send`
subdomain Memberstack needs. Do not remove them while tidying.

⚠️ **But do not use them in a mail client.** Checked 1 Sep 2026:
`imap.barna.co.uk` and `smtp.barna.co.uk` resolve correctly, but the
server presents a certificate for `*.stackmail.com` only, so TLS fails on
a hostname mismatch. Outlook, Apple Mail and anything else must be
pointed at the real hostnames instead.

#### Mail client settings for `info@barna.co.uk`

| Setting | Value |
|---|---|
| Incoming | IMAP, `imap.stackmail.com`, port 993, SSL/TLS |
| Outgoing | SMTP, `smtp.stackmail.com`, port 465 SSL/TLS (or 587 STARTTLS) |
| Username | the full address, `info@barna.co.uk`, not `info` |
| Password | the mailbox password |
| Outgoing auth | required — the server offers PLAIN, LOGIN and CRAM-MD5 |

In Outlook, choose manual setup and pick **IMAP**. Letting it autodiscover
tends to guess Exchange or Outlook.com and fail confusingly.

Zone verified 1 Sep 2026 after the mailbox was created: four GitHub A
records, `www` CNAME, apex MX and one apex SPF all unchanged, no wildcard
`*` record, and `https://barna.co.uk` still 200.

Role addresses for everyone else (`treasurer@`, `membership@`, `chair@`)
should be free **forwarders** pointing at personal inboxes, not mailboxes
— when someone steps down you change the forward instead of hunting for
logins. `info@` is the exception because it has to receive. Forwarders
appear to live under the same domain management screen and to sit outside
the one-mailbox limit, but that was not confirmed against a live account,
so check it rather than promising anyone an address.

### 4b. Point Memberstack at it

Memberstack → **Settings → Email Sender Address** → enter
`info@barna.co.uk`. It shows **one MX and two TXT** records, then a
**Verify** button in the same modal — the values are generated per account
so they must be read at the time, but the *shape* is now known.

Memberstack sends through **Resend**, and Resend puts its records on a
`send` subdomain rather than the apex:

| Type | Name | Value | Priority |
|---|---|---|---|
| MX | `send` | `feedback-smtp.<region>.amazonses.com` | 10 |
| TXT | `send` | `v=spf1 include:amazonses.com ~all` | — |
| TXT | `resend._domainkey` | `p=<long key>` | — |

### ⚠️ Two worries this resolves, and one that remains

**The MX is not a conflict.** Earlier notes warned that Memberstack asking
for an MX threatened the existing `mx.stackmail.com`. It does not: Resend's
MX is on `send.barna.co.uk`, a different name entirely. The apex MX stays
exactly as it is. **Do not touch the apex MX**, and if Memberstack ever
displays an MX whose Name is `@` or blank, stop and check before saving —
that would break mail.

**No SPF merge is needed either.** Resend's `v=spf1 include:amazonses.com`
also lives on `send`, not the apex, so the existing apex record
`v=spf1 include:spf.stackmail.com a mx ~all` is untouched. The "only ever
one SPF record" rule in section 2 still holds — it applies per name, and
these are two different names, each with one record.

**What does still apply: 20i's Name field.** Enter `send` and
`resend._domainkey` on their own — 20i appends the domain automatically,
so typing `send.barna.co.uk` produces `send.barna.co.uk.barna.co.uk` and
silently does nothing (section 10). Subdomain entries behave correctly,
which is why this job avoids the apex pain that the A records hit.

Resend also tells you to **omit the domain from pasted values**. That is
advice for the Name field, not the value field — paste MX and DKIM
*values* exactly as given, in full.

Propagation can take up to 24 hours, though 20i is usually minutes. Click
Verify in Memberstack after the records resolve, not before.

### 4c. Check it

```
dig +short MX  barna.co.uk            # must still be 10 mx.stackmail.com
dig +short TXT barna.co.uk            # must still be the stackmail SPF, one record
dig +short MX  send.barna.co.uk       # the new Resend feedback MX
dig +short TXT send.barna.co.uk       # v=spf1 include:amazonses.com ~all
dig +short TXT resend._domainkey.barna.co.uk
```

The first two lines are the safety check: if either changed, mail for the
domain is at risk and the apex records need putting back.

Finally, trigger a real password reset from the live site and confirm it
arrives from `info@barna.co.uk` and lands in the inbox rather than spam.
That, not the green tick in Memberstack, is what the whole exercise is for.

---

## 5. DMARC (currently missing)

The domain has SPF but no DMARC, which weakens deliverability and
leaves the domain easier to spoof. Add once the mail setup is settled
and working, not before:

```
TXT   _dmarc   v=DMARC1; p=none; rua=mailto:info@barna.co.uk
```

`p=none` only monitors and changes nothing about delivery, which is the
correct place to start. Tightening to `quarantine` or `reject` is a
later job, only after confirming legitimate mail passes.

---

## 6. Suggested order

Doing these one at a time makes it obvious what broke if something does.

0. **Commit the `CNAME` file** (section 3). Costs nothing, breaks
   nothing, and without it every later DNS change fails. Done Aug 2026.
1. Get control of the domain and DNS. Confirm you can log in and see the
   existing records.
2. If moving hosts, recreate MX and SPF at the new host **first**, and
   confirm mail still works.
3. Repoint the A records and the www CNAME at GitHub Pages (section 3).
   Wait for it to resolve, then check the site loads on barna.co.uk.
4. Enable Enforce HTTPS once GitHub verifies the domain.
5. Add `barna.co.uk` to Memberstack's allowed domains, or the login and
   signup modals will not work on the new address.
6. Create the mailbox for Memberstack (e.g. `info@barna.co.uk`) and
   confirm you can send and receive from it.
7. Add Memberstack's DKIM records, verify the sender in their dashboard,
   and send a test signup to confirm the welcome email arrives.
8. Add DMARC.
9. Retire the old Weebly site.

Note this reverses the original advice, which put the website move last
after email was proven. That order was written when the domain handover
looked slow and email looked quick. In practice it is the other way
round: the website move is a single DNS change with a known-good
rollback, while the email side is blocked on getting a real mailbox. The
site move no longer needs to wait for it. The MX and SPF records are
untouched by the A record change, so moving the website first cannot
affect email either way.

---

## 7. Checking your work

Run these from Terminal. They read public DNS, they change nothing.

```bash
dig +short A barna.co.uk        # expect the four 185.199.x.153 addresses
dig +short CNAME www.barna.co.uk # expect barnawebsite.github.io.
dig +short MX barna.co.uk        # expect your mail host, never empty
dig +short TXT barna.co.uk       # expect exactly ONE v=spf1 line
dig +short TXT _dmarc.barna.co.uk
```

DNS changes are not instant. Allow up to a few hours, occasionally 24,
before concluding something is wrong. If `dig` still shows old values,
that is usually caching rather than a mistake.

---

## 8. Gotchas

- **Lower the TTL before cutover if you can.** Setting it to 300
  seconds a day ahead means mistakes are undone in minutes rather than
  hours.
- **The apex domain cannot be a CNAME.** That is why it needs four A
  records rather than pointing at `barnawebsite.github.io` directly.
  Some hosts offer ALIAS or ANAME records, which do the same job.
- **Deleting the `CNAME` file** from the repo silently unsets the custom
  domain. It gets recreated by GitHub when you re-save the setting.
- **"There isn't a GitHub Pages site here."** on barna.co.uk does not
  mean the DNS is wrong. It means the DNS is right and arriving at
  GitHub, but the `CNAME` file or Pages custom domain setting is
  missing, so GitHub cannot tell which repo the request is for. Fix the
  GitHub side, do not touch the DNS.
- **Memberstack has its own domain allowlist.** Signup, login and the
  gated members area are checked against it. `barna.co.uk` needs adding
  in the Memberstack dashboard or the members area will break on the new
  address while working fine on github.io.
- **The domain renews May 2027.** Whoever holds it needs to actually
  receive that reminder. Getting invoices to a current officer is what
  started this whole exercise.

---

## 9. Nominet registrant and data quality (Aug 2026)

Separate job from the DNS above, but time limited, so it is written down.

**Where it stands.** Alan Jewitt updated the domain's contact details at
Nominet to Michele Converso. The WHOIS now reads:

| Field | Value |
|---|---|
| Registrant | **Abacus Computer Training** (wrong, historic) |
| Organisation type | UK Registered Charity |
| Organisation number | 1039150 (BARNA's charity number) |
| Trading name | British Anaesthetic and Recovery Nurses Association |
| Contact | Michele Converso, `michele.converso@hotmail.it` |
| Data Quality | **Awaiting validation** |

**Why it is probably failing validation.** Nominet checks the registrant
name and address against third party data sources. The record now claims
to be UK Registered Charity 1039150, but charity 1039150 is named
British Anaesthetic and Recovery Nurses Association, not Abacus Computer
Training. Those cannot match. Waiting for validation to pass on its own
is therefore unlikely to work; the name has to be corrected.

**Why it matters.** Nominet's data quality process applies a data
quality lock after 30 days if the data stays unvalidated. That suspends
the domain, which stops the website and any email on it from working,
and a suspended domain can no longer be modified or transferred.
Nominet does **not** delete domains suspended this way, so this is
recoverable, but it would take the site down.

**Who does the fix.** A registrant name change is a Nominet "Registrant
Transfer", £10 plus VAT, initiated by whoever controls the domain's
admin contact email. That is now Mike, which is why Alan said he can no
longer do it himself. Steps:

1. Activate a free Nominet Online Services account using
   `michele.converso@hotmail.it` (the "first time logging in" page
   emails a password link). Login is tied to that exact address.
2. Select barna.co.uk, choose "transfer domain", enter the new
   registrant email, pay the £10 plus VAT.
3. Accept the transfer from the email **within 5 days** or it times out
   and the fee is refunded. On accepting, enter BARNA as the registrant:
   British Anaesthetic and Recovery Nurses Association, UK Registered
   Charity, 1039150.
4. Use an address that will validate against a third party source for
   the charity, ideally BARNA's registered charity address rather than
   an individual's.

**This does not block section 3.** The A records and the website move
are independent of the registrant name. Do not let the Nominet job hold
up the cutover.

---

## 10. Taking full control: moving off SYPO

The website is live, but DNS still sits on `ns1–4.stackdns.com`, which is
Sypo's platform and nobody at BARNA has a login for. That is the only
reason repointing the site needed emails to Alan. Moving the registrar is
what fixes it permanently.

Three separate layers, easy to confuse:

| Layer | Who holds it (Aug 2026) | How to change it |
|---|---|---|
| Registrant (legal owner) | **BARNA** ✅ already done | Nominet, registrant transfer |
| Registrar (manager) | Web by Numbers, tag `SYPO` | Nominet → **Change Registrar** |
| DNS hosting | `stackdns.com` | nameservers, at the new host |

### Records that must exist at the new host BEFORE the switch

Copy these exactly. Everything starts blank at a new host, and anything
missed here breaks silently.

```
A      @      185.199.108.153
A      @      185.199.109.153
A      @      185.199.110.153
A      @      185.199.111.153
CNAME  www    barnawebsite.github.io.
MX     @      10 mx.stackmail.com          <- see warning below
TXT    @      v=spf1 include:spf.stackmail.com a mx ~all
```

### ⚠️ The MX is a trap on this particular move

`mx.stackmail.com` **is Sypo's own mail platform**. Once BARNA leaves
Sypo, that mailbox host may stop accepting mail for the domain. Copying
the MX across verbatim would then leave a record pointing at a dead
server, which silently blackholes anything sent to `@barna.co.uk` rather
than bouncing it.

No `@barna.co.uk` mailboxes are actually in use, so nothing is lost today.
But decide deliberately at the time:
- moving mail to a new provider → point MX at **them**, and update the
  SPF `include:` to match
- not setting up mail yet → it is more honest to remove the MX than to
  leave one aimed at a host that no longer serves the domain

Only ever one SPF record. Merge, never add a second.

### DONE (1 Sep 2026): moved to 20i, not Cloudflare

Cloudflare was the first choice on technical merit but was dropped: it
requires the domain to be **active on Cloudflare DNS before** you can buy
the registration, and Nominet does not let a registrant change
nameservers. That needed the old registrar's help. 20i needed nobody.

What actually happened, and the two things that caught us out:

1. **The Nominet registrar change cost £12, not £0.** The intro page said
   "our fee of £0.00 plus VAT"; the summary page charged £10 plus VAT.
   Alan could likely have pushed the tag for free from the registrar side.
   Paid it for independence.
2. **20i's tag is `STACK`.** Not `20I`. `PROSTACK` sits directly beneath
   it in Nominet's registrar search, so read the entry, not the position.
3. **20i creates a FRESH, EMPTY zone when a domain lands. It does not
   copy the live one.** The new zone pointed the apex at 20i's parking IP
   `185.151.30.138`, had a wildcard `*` A record, no `www`, and an SPF
   ending `-all` instead of `~all`. Saving it as-is would have taken the
   site down. The live site kept working only because the old reseller's
   zone was still answering. **Always compare the new zone against `dig`
   output before trusting it.**
4. **20i's DNS Name field appends the domain, and `@` auto-expands.**
   Typing `barna.co.uk` produced `barna.co.uk.barna.co.uk`, a subdomain
   that silently does nothing. Getting apex records in took support's
   help. Subdomain entries (`www`) work as expected.

The zone was then made an exact match for what was already live, so it no
longer matters which zone is authoritative.

### Superseded: the Cloudflare plan (31 Aug 2026)

Email is deliberately **not** moving with it. BARNA's shared Google account
is Jane's personal one with live correspondence running through it, so that
is an organisational conversation, not a technical task. Memberstack does
not need a barna.co.uk address either — it sends from its own default.
Cloudflare Email Routing can forward `info@barna.co.uk` to a personal inbox
for free later, without a mailbox, if that is ever wanted.

Why Cloudflare: supports `.co.uk`, free DNS, domains at cost with no
markup, no bundled web hosting or mailboxes to pay for. No transfer fee,
and `.uk` transfers do not add a year, so the 15 May 2027 expiry stands.

#### ⚠️ The order is strict and getting it wrong auto-rejects the transfer

Cloudflare requires the domain to be **Active on Cloudflare DNS before**
you can buy the registration. And from their docs: *"if you request your
current registrar to update the IPS tag before completing the checkout
process, the transfer request will be automatically rejected."* Their
forum is full of `.uk` domains stuck exactly this way.

Nominet Online Services does **not** expose nameserver editing to
registrants, so Sypo has to make two of these changes:

1. Add barna.co.uk to Cloudflare, free plan.
2. **Check every record imported.** Cloudflare's scan misses things. Compare
   against the list above: four A records, www CNAME, MX, SPF. This is where
   email dies if you are careless.
3. Set the A records and www CNAME to **DNS only** (grey cloud, not orange).
   GitHub Pages behind a Cloudflare proxy works, but with Enforce HTTPS on,
   a wrong SSL mode gives redirect loops. Grey cloud keeps behaviour
   identical to today. Turn proxying on later, deliberately, on its own.
4. **Ask Sypo** to point the nameservers at Cloudflare's two.
5. Wait for the Cloudflare zone to read **Active**. Do not skip ahead.
6. Complete the Cloudflare Registrar checkout.
7. **Only now** ask Sypo to change the IPS tag to `CLOUDFLARE`.
8. Verify with the `dig` commands in section 7.

### Order (generic, if not going to Cloudflare)

1. Choose the host and create the account. Needs DNS control and, if mail
   is going there too, mailboxes. Web hosting is **not** needed — the site
   is on GitHub Pages.
2. Build the full DNS zone there, using the records above, with the MX
   decision made.
3. Get the new registrar's **Nominet tag** (e.g. `123-REG`, `20I`).
4. Nominet Online Services → select barna.co.uk → **Change Registrar** →
   enter the tag. This is *not* "Transfer Domain", which changes the owner.
5. Point the nameservers at the new host.
6. Verify with the `dig` commands in section 7 before assuming it worked.
   The site must still load and the MX must still resolve.

Nothing changes on the GitHub side. The `CNAME` file stays exactly as it
is and the site keeps working, provided those four A records land
identically.

### After the move, this becomes possible

- Repointing the site at anything else is four A records in a control
  panel, no third party involved.
- The Memberstack custom email sender (one MX, two TXT) can finally be set
  up, which is what makes onboarding the 91 legacy members respectable.
- DMARC (section 5) can go in.

---

## 11. Outstanding, as of 31 Aug 2026

Live and working: domain, HTTPS, Memberstack in live mode, payments,
discount codes, gated members area.

**Done:** domain, HTTPS, Memberstack live, payments, discount codes, gated
members area, and full control of registrant, registrar and DNS.

**Agreed order (1 Sep 2026), Mike's call:**

1. **`info@barna.co.uk` created 1 Sep 2026** ✅ — free, no hosting package
   needed. Still to do: set it as Memberstack's
   sender (**Settings → Email Sender Address**). Reordered ahead of the
   members on 1 Sep 2026: onboarding 91 people is the one job where mail
   landing in spam is expensive, and DNS is now in hand so there is no
   reason to wait. Memberstack will give one MX and two TXT records.
   The MX turns out **not** to threaten the existing `mx.stackmail.com`:
   Resend puts it on `send.barna.co.uk`, not the apex. Section 4 has the
   full record shape and the safety checks.
2. **Onboard the ~91 legacy members** onto the Manual Access plan, each with
   an `accessexpiresat` date. See the expiry section in `CLAUDE.md`. Note
   the Admin API cannot set a password on an existing member, so every one
   of them sets their own via a reset email. Send a test batch of five
   before doing all 91.

   Checked 1 Sep 2026, two prerequisites are missing before this can start:
   - **There is no member list in the repo.** Names, emails and each
     person's real expiry date have to be exported from wherever the
     legacy records actually live. Nothing can be scripted until that
     exists.
   - **There is no import script.** `scripts/check_member_expiry.py` is
     only the removal half. A create/onboard script has to be written; it
     should reuse that file's patterns — `https://admin.memberstack.com`,
     the `X-API-KEY` header, `require_env` for config, and above all
     **dry run by default**.

   ⚠️ **This repo is public.** A spreadsheet of 91 members' names and email
   addresses must never be committed to it. Keep the list outside the repo
   entirely, or add it to `.gitignore` *before* it is saved anywhere near
   the working directory, the way `_to-upload-google-drive/` is handled.
3. **Move the money off personal details.** Three separate places, all
   currently pointing at an individual:
   - **Stripe**: membership payments land in Mike's personal bank account.
     Swap to BARNA's account and sort code. Most urgent of the three, since
     it is charity income going to a trustee.
   - **Memberstack**: the £11/month subscription is on a personal card.
   - **20i**: the domain renewal card, and the account's only login email.
     Once `info@barna.co.uk` exists, move the login to it.

Note: Memberstack's default sender (`no-reply@memberstack.io`) does work, so
the mailbox is about deliverability rather than possibility. It is first in
the list because a bulk onboarding is exactly when spam-foldering hurts.

**Also outstanding:**
- Memberstack custom email sender + its DKIM records (section 4).
- Onboard the ~91 legacy members onto Manual Access with `accessexpiresat`
  dates. Possible today via Memberstack's default sender, but better after
  the custom sender exists.
- DMARC (section 5).
- Retire the old Weebly site.

**Small, independent:**
- Rotate the `info@barna.co.uk` mailbox password. It was exposed in a
  screenshot on 1 Sep 2026 and deliberately kept for now to avoid
  reconfiguring Outlook mid-setup. Changing it means updating the IMAP and
  SMTP passwords in Outlook at the same time.
- 50% student discount code in Stripe, if still wanted.
- Update the `MEMBERSTACK_SECRET_KEY` repo secret with a **Live** Admin API
  key. `MANUAL_ACCESS_PLAN_ID` does *not* change — verified identical in
  both modes.
- Confirm the `accessexpiresat` custom field exists in Live.
- Untick the two WHOIS privacy flags at Nominet if still set. A charity is
  not eligible for the opt-out, and the address is public on the charity
  register anyway.
- The 20i account is registered to BARNA as an organisation, but the only
  login email on it is a personal one. Add a second user, or move it to a
  `@barna.co.uk` address once one exists. This is the exact failure the
  whole exercise was fixing, so do not let it settle.
