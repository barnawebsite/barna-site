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

#### Four stackmail CNAMEs live in the zone — leave them alone

These are mail client autodiscovery records, not cruft. They are **not**
in the original zone list further down this document, which was only ever
the minimal must-exist set rather than a full dump:

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

They were first noticed on 1 Sep 2026, right after the mailbox was created,
and initially written up here as having been added by that step. That was
probably wrong: the zone's SOA serial still read 31 Aug 15:36 afterwards,
so the zone had not been written that day and the records almost certainly
predate the mailbox. Do not expect creating a mailbox to generate DNS.

Zone verified 1 Sep 2026 after the mailbox was created: four GitHub A
records, `www` CNAME, apex MX and one apex SPF all unchanged, no wildcard
`*` record, and `https://barna.co.uk` still 200.

#### ⚠️ 20i's DNS editor does not save as you type

Adding rows fills in the form only. The zone is untouched until an explicit
save at the bottom of the page. On 1 Sep 2026 all three Resend records
looked correct on screen while none of the four `ns*.stackdns.com`
nameservers had them.

The quick way to tell the difference, rather than assuming propagation
delay:

```
dig +short SOA barna.co.uk @ns1.stackdns.com
```

The first number is a unix timestamp of the last zone write. If it predates
the edit, nothing was saved and waiting will not help.

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

#### ⚠️ RESOLVED 1 Sep 2026: a second 20i account still held DNS authority

All three records were entered correctly, `Update DNS` was clicked, and the
panel confirmed "Your changes have been saved". They still do not exist in
DNS:

- absent from **all four** of `ns1` to `ns4.stackdns.com`
- all four report the identical SOA serial `1788187007`, which is
  **31 Aug 2026 15:36**, so the zone has not been written since the day
  before the edit
- still absent after a 7 minute poll

Leading theory, and it fits the history in section 10: when the domain
landed at 20i a **fresh empty zone** was created alongside the old
reseller's zone, and the old one is still the zone answering queries.
Making the two match at the time hid the problem rather than solving it,
because identical zones give identical answers right up until you add a
record to one of them. The note in section 10 saying "it no longer matters
which zone is authoritative" is wrong, and this is how it surfaced.

**20i support confirmed exactly this** and fixed it in minutes: *"another
20i account has a barna.co.uk package which currently has authority"* —
the old reseller's. Because the domain itself sits in BARNA's account they
were able to move authority across. Serial jumped to 15:29 and all three
records went live immediately, reaching Cloudflare and Google DNS within
minutes.

Lessons worth keeping:
- **Owning the domain is not the same as holding its DNS authority.** Both
  can sit in different 20i accounts, and the panel gives no hint which one
  is winning. Section 10's "it no longer matters which zone is
  authoritative" was wrong, and reconciling the two zones is what hid it.
- **The SOA serial is the tell.** A frozen serial after a successful save
  means the zone answering queries is not the zone being edited. That check
  turned a propagation guess into a five minute support ticket.
- **Before an authority move, verify the receiving zone is complete.** It
  becomes live the instant they switch, so anything missing breaks the site
  and mail at that moment.

Mail and the website were unaffected throughout: apex MX, apex SPF, the A
records, `www`, the stackmail CNAMEs, absence of a wildcard, mail
acceptance for `info@`, and `https://barna.co.uk` were all re-verified
after the switch.

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

## 5. DKIM and DMARC for mail sent from `info@` (the Yahoo bounce)

### What happened, 2 Sep 2026

A mailout to the members from `info@barna.co.uk` hard-bounced for twelve
recipients with a 550 at `RCPT TO`:

```
550-"Please enable DKIM for your domain. Yahoo requires all senders to
550 authenticate with DKIM - https://senders.yahooinc.com/best-practices/"
```

Every one of the twelve was `yahoo.com`, `yahoo.co.uk`, `aol.com` or
`sky.com`. That is one platform, not four: Yahoo runs AOL's and Sky's mail.
So this is a single provider refusing the domain, not a scatter of unrelated
failures, and everyone else received the mail normally.

**Nothing is wrong with the mailbox, the message or 20i's relay.** Since
February 2024 Yahoo and Google require senders to authenticate with SPF
*and* DKIM and to publish a DMARC record. `barna.co.uk` has SPF and neither
of the other two. The rejection arriving at `RCPT TO`, before the message
body is ever transmitted, is the tell: it is a policy check on the sending
domain, nothing to do with content.

Confirmed by `dig` on 2 Sep 2026:

| Record | State |
|---|---|
| apex SPF | present, exactly one record, unchanged |
| DKIM | **none** — no selector resolves on the domain |
| `_dmarc` | **none** |

⚠️ **`resend._domainkey.barna.co.uk` does not count.** It exists and it is
correct, but it signs mail *Memberstack* sends through Resend from
`send.barna.co.uk` (section 4b). Mail Mike sends from the `info@` mailbox
leaves through StackMail's relay and is signed by nothing. Two different
senders need two different DKIM keys. Do not read the Resend record as
"DKIM is done".

### 5a. Turn on DKIM signing at 20i

20i's own documentation puts the tool at **Manage Hosting → the package →
Email → DomainKeys**. BARNA had no hosting package (section 4a), so that
path did not exist in the panel at all.

#### ⚠️ CONFIRMED 2 Sep 2026: DKIM is NOT available on the domain screen

Checked in the panel. **Manage Domain Names → `barna.co.uk` → Options →
Manage** offers, in full:

- Domain Management: Manage DNS, Domain Contacts, WHOIS, Nameservers,
  Domain Privacy, DNSSEC Protection, Domain Forwarding, Renew Domain,
  Free Web Hosting, Transfer Away, Add Hosting Package
- Email Management: Email Accounts, Email Forwarders, Catch-All
  Forwarders, Autoresponders, Send-only Addresses, Receive-only
  Addresses, Junk Mail Filters

No DomainKeys. No DKIM. So this cannot be self-served from the domain, and
the mailbox-only setup that section 4a is otherwise right to recommend has
this one real gap.

#### ⚠️ Adding the TXT record by hand does NOT work

Tempting, because Manage DNS is right there. It achieves nothing. DKIM is a
*signature applied by the sending server*, and the TXT record only publishes
the public key that verifies it. StackMail's relay has to be told to sign;
until it does, a published key just advertises a signature that never
arrives. Do not spend time hand-crafting a record.

#### 20i's answer, 2 Sep 2026: a package is mandatory

Arron H at 20i support: *"In order to set up a DKIM record, the domain must
be assigned to a hosting package. With the free web hosting, a hosting
package will be created for the domain, so you would be able to access and
use our DKIM tool."*

So there is no mailbox-only route to DKIM. **Free Web Hosting** (on the
Manage Domain Names screen, alongside Add Hosting Package) is the way in,
and it costs nothing.

⚠️ **They did not answer the second question**, the one that actually
carried the risk: whether attaching the package preserves the existing
`info@` mailbox. The reply was "try it and let us know if there are
issues", which is not a guarantee. And there is a second hazard neither
side raised in the ticket: **attaching a hosting package normally makes the
host write its own A records for the domain**, which would take the apex off
GitHub Pages and drop the website.

Mitigating both is cheap, so do that rather than seek a better answer:

- `dns-snapshot-2026-09-02.txt` at the repo root is a full pre-change dump
  of the zone taken from `ns1.stackdns.com`. If the package overwrites
  anything, the correct values are in there and DNS is editable directly in
  Manage DNS, so a rollback is minutes.
- The mailbox itself was created 1 Sep 2026 and holds about a day of mail,
  so the data at risk is close to nothing. It is the *address* working that
  matters, and a mailbox can be recreated.

**Check order after taking the free package, before touching DKIM:** apex A
records still the four `185.199.x.153`, apex MX still `mx.stackmail.com`,
apex TXT still one SPF, `https://barna.co.uk` still 200, and
`info@barna.co.uk` still listed and still able to receive. Only once all of
that passes is it safe to go on to the DomainKeys tool.

#### ⚠️ WHAT THE FREE PACKAGE ACTUALLY DID, 2 Sep 2026: it took the site down

It was worse than "may overwrite the A records". Attaching Free Web Hosting
rewrote the zone the moment it was created, and `https://barna.co.uk`
stopped answering. Full diff against `dns-snapshot-2026-09-02.txt`:

| Record | Before | After the package |
|---|---|---|
| apex `A` | four GitHub IPs | **`185.151.30.226`** (20i) |
| apex `AAAA` | none | **`2a07:7800::226`** added |
| `*` `A` | none | **`185.151.30.226`** added |
| `*` `AAAA` | none | **`2a07:7800::226`** added |
| apex SPF | ends `~all` | **ends `-all`** |
| `autodiscover`, `ftp` CNAMEs | absent | added (harmless, left in place) |
| apex `MX`, `www`, `send.*`, `resend._domainkey`, imap/mail/pop3/smtp | — | **all untouched** ✅ |

Two things to take from that. **The AAAA records are the trap**: DNS-only
checks that look at `A` will say the zone is fine while IPv6 visitors still
land on 20i. And **the SPF qualifier change is silent** — `-all` instead of
`~all` is a hard fail rather than a soft one, which is the kind of thing
that surfaces a week later as mysterious bounces.

**Nothing about mail broke.** The MX and every mail CNAME survived, which
is the one genuinely good piece of news.

##### Fixing it: edit in place, do not add

Section 10's gotcha 4 says 20i's Name field mangles apex entries and getting
apex records in previously took support's help. That does not apply here,
because the package leaves apex rows *already present* with editable Data
boxes. So:

1. **Edit** the existing apex `A` Data box to `185.199.108.153`.
2. **Remove** `*` `A`, `*` `AAAA` and apex `AAAA`.
3. **Edit** the apex TXT back to `v=spf1 include:spf.stackmail.com a mx ~all`.
4. **Update DNS**.

GitHub Pages is happy on a single A record, so one is enough to restore
service; the other three are redundancy and can wait. Done this way the
site came back within minutes, verified against all four `stackdns.com`
nameservers and five public resolvers, with the Let's Encrypt certificate
for `barna.co.uk` intact.

##### The fallout lasted longer than the outage, and here is why

The zone was wrong for about seven minutes. People were still seeing the
wrong site nearly an hour later, which caused more alarm than the outage
itself.

**Records are handed out with a 3600 second TTL, not the 300 in the SOA.**
So anyone who loaded the site during the bad window cached it for up to a
full hour *from their own lookup*, and nothing done at the DNS end speeds
that up. Budget an hour of tail, and say so up front rather than promising
a five minute fix.

**The IPv6 record is what makes it stick.** macOS caches in
`mDNSResponder`, browsers cache on top of that, and Safari prefers IPv6 —
so `dig` reports the zone as correct while the browser keeps going to 20i.
The local fix is a flush plus a full quit of the browser:

```
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

The fastest way to prove the site is actually fine, for anyone who reports
it broken: load it on a phone with wifi off. Different resolver, no cache.

##### ⚠️ The old 2012 site is still live in the old reseller's 20i package

`185.151.30.226` does not serve a holding page. It serves the **original
pre-Weebly BARNA site**, the one with the 2012 annual conference on the
front. That is what appeared during the outage, which is why it looked so
much worse than a normal misconfiguration.

It sits in the old reseller's hosting package, the same one that held DNS
authority until 1 Sep 2026 (section 4b). It is unreachable unless DNS
points at it, so it is harmless where it is, and it has no working login:
its only member link is `members.htm`, a static page with no form. But it
is one more reason to get that old package deleted rather than left
lying around.

##### If the package is ever removed or re-added, re-check the zone

The rewrite happened on attach with no warning and no prompt. Assume any
change to the hosting package can do it again, and always diff against the
snapshot afterwards rather than trusting the panel.

#### The tool, once the package exists

- Selector: any name will do. `default` is fine.
- Click **Add Signature**. Because the nameservers are 20i's own
  (`ns1-4.stackdns.com`), 20i writes the TXT record into the zone itself.
- Signing starts on the next message sent; DNS then has to resolve before
  Yahoo will accept it.

⚠️ **Verify the record actually landed.** The 20i DNS editor's silent
no-save (section 4a) and the split-authority problem (section 4b) both bit
this domain already. Use the SOA serial check, not patience.

### 5b. Then add DMARC

Previously filed here as optional. It is not: Yahoo and Google both want a
DMARC record present alongside SPF and DKIM. Add it once DKIM is signing
and verified, not before, or a strict policy could start failing legitimate
mail.

```
TXT   _dmarc   v=DMARC1; p=none; rua=mailto:info@barna.co.uk
```

`p=none` only monitors and changes nothing about delivery, which is the
correct place to start. Tightening to `quarantine` or `reject` is a later
job, only after confirming legitimate mail passes.

### 5c. Check it

```
dig +short TXT default._domainkey.barna.co.uk   # or whatever selector was used
dig +short TXT _dmarc.barna.co.uk
dig +short TXT barna.co.uk                      # still exactly ONE SPF record
dig +short MX  barna.co.uk                      # still 10 mx.stackmail.com
```

The last two lines are the safety check from section 2, and they matter
here too: a DKIM change should not touch the apex SPF or MX at all.

Then send a real test to a `yahoo.co.uk` address and to a Gmail address.
In Gmail, **Show original** must report `PASS` for SPF, DKIM *and* DMARC.
That, not a green tick in the 20i panel, is the proof.

Finally, re-send to the twelve that bounced. They received nothing at all,
so they are not duplicates.

### 5d. Worth knowing for the next mailout

The twelve bounces are the visible part. Mail that is accepted is not
necessarily mail that reaches an inbox, and an unauthenticated domain
sending to ninety-odd recipients at once from a shared mailbox is the exact
pattern spam filters are built to catch. DKIM and DMARC fix the hard
failures; for regular mailouts to the whole membership a proper bulk sender
with unsubscribe handling is the better long-term answer than webmail.

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
8. Turn on DKIM for the `info@` mailbox at 20i, then add DMARC
   (section 5). Yahoo, AOL and Sky reject the domain outright without it.
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

### Drafted 20i support ticket: DKIM for `info@` (2 Sep 2026)

Send from the 20i panel, **Help & Support**. Verified 2 Sep 2026 that there
is no self-serve route, so this ticket is the next step and not a fallback.

> Subject: Enable DKIM signing for barna.co.uk outbound email
>
> Hello,
>
> barna.co.uk is in my 20i account with a single StackMail mailbox,
> info@barna.co.uk, and no hosting package attached. The nameservers are
> ns1 to ns4.stackdns.com.
>
> Mail sent from that mailbox is being rejected by Yahoo, AOL and Sky with
> a 550 error at RCPT TO saying "Please enable DKIM for your domain. Yahoo
> requires all senders to authenticate with DKIM". Twelve recipients
> bounced on a recent mailout to our members. The domain publishes SPF but
> has no DKIM record.
>
> Your DomainKeys tool is documented under Manage Hosting. There is no
> DomainKeys option on the Manage Domain Names screen for this domain,
> which I assume is because no hosting package is attached.
>
> Could you please either:
>
> 1. Enable DKIM signing for outbound mail from info@barna.co.uk and
>    publish the matching TXT record in the zone, or
> 2. Confirm whether attaching the Free Web Hosting package would give me
>    the DomainKeys tool, and whether doing so keeps the existing
>    info@barna.co.uk mailbox and all of its stored mail intact. I do not
>    want to risk breaking a working mailbox to reach a settings screen.
>
> Thank you,
> Mike

**Also outstanding:**
- **DKIM for the `info@` mailbox (section 5).** Now urgent rather than
  tidy: as of 2 Sep 2026 Yahoo, AOL and Sky reject mail from the domain
  outright. Twelve members bounced on the first real mailout.
- Memberstack custom email sender + its DKIM records (section 4).
- Onboard the ~91 legacy members onto Manual Access with `accessexpiresat`
  dates. Possible today via Memberstack's default sender, but better after
  the custom sender exists.
- DMARC (section 5b) — required by Yahoo and Google, not optional.
- Retire the old Weebly site.
- **Get the old reseller's 20i hosting package deleted.** It still holds a
  working copy of the pre-Weebly 2012 site, which surfaced publicly during
  the 2 Sep 2026 outage (section 5a).

**Small, independent:**
- Rotate the `info@barna.co.uk` mailbox password. It was exposed in a
  screenshot on 1 Sep 2026 and deliberately kept for now to avoid
  reconfiguring Outlook mid-setup. Changing it means updating the IMAP and
  SMTP passwords in Outlook at the same time.
- 50% student discount code in Stripe — still outstanding, confirmed not
  created as of 1 Sep 2026. Exact spec is in `CLAUDE.md` under "Discount
  codes live in Stripe"; must be entered in **Live** mode.
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
