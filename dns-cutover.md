# barna.co.uk DNS cutover pack

Everything needed to point barna.co.uk at the new site and get member
emails working, prepared in advance so the handover day is copy and paste
rather than research. Written for whoever holds the DNS control panel,
which as of Aug 2026 is being transferred from Web by Numbers / Sypo.

**Read the "Do not break email" section before changing anything.**

---

## 1. What is live right now (Aug 2026)

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

**The exact values are generated per account and cannot be written down
in advance.** Get them at the time: Memberstack → Emails → Add
transactional sender → enter the address (e.g. `info@barna.co.uk`) → it
will display the records to add.

Expect roughly:
- **2–3 CNAME records** for DKIM, with names like `s1._domainkey`,
  pointing at Memberstack's mail provider. Add these exactly as given.
- **Possibly an SPF change.** If they ask for an `include:`, merge it
  into the existing SPF record rather than creating a second one:

  ```
  v=spf1 include:spf.stackmail.com include:THEIR-VALUE-HERE a mx ~all
  ```

A real mailbox is needed for the sender address, not just a forwarder,
since it has to receive the verification email. Role addresses for
everyone else (`treasurer@`, `membership@`, `chair@`) can be free
forwarders pointing at personal inboxes, which is the right pattern —
when someone steps down you change the forward instead of hunting for
logins.

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
