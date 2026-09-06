# Eventbrite: removed from the site 6 Sep 2026, kept here in case it comes back

Eventbrite was retired when webinars moved to one permanent Teams link in the
members area. See the Webinars section of `CLAUDE.md` for why.

Nothing here is lost: it is all in git history too. This file exists so it can
be put back without going digging.

## The account

- Organiser page: `https://www.eventbrite.com/o/british-anaesthetic-recovery-nurses-association-113028693951`
- Member booking code: `BARNAVIP`

The Eventbrite account itself was **not** closed. Only the links to it were
taken off the website.

## To put it all back in one command

```
git revert <the commit that removed it>
```

Or take individual pieces from the commit before it. The three things removed
are reproduced below exactly as they were.

## 1. Footer social icon (was on all 12 pages)

Sat inside `<div class="footer-social">` in the shared footer, after the
LinkedIn icon. The glyph is a generic ticket, not Eventbrite's real logo mark.

```html
      <a href="https://www.eventbrite.com/o/british-anaesthetic-recovery-nurses-association-113028693951" target="_blank" rel="noopener" aria-label="BARNA events on Eventbrite" title="Eventbrite">
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round">
          <path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h15A1.5 1.5 0 0 1 21 7.5v2.1a2.4 2.4 0 0 0 0 4.8v2.1a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 16.5v-2.1a2.4 2.4 0 0 0 0-4.8V7.5Z"/>
          <path d="M14 6v2M14 11v2M14 16v2" stroke-linecap="round"/>
        </svg>
      </a>
```

## 2. The CTA band on `members.html`

Sat immediately below the "Welcome back" section, inside the gated
`data-ms-content="barna-members-area"` block.

```html
  <!-- ============ 1. EVENTBRITE CTA BAND ============ -->
  <section class="cta-band">
    <div class="wrap">
      <p style="max-width:640px; margin:0 auto 6px;">As a member, you'll get free or discounted access to all our webinars and more.</p>
      <p class="promo-code-line">Your code: <span class="promo-code">BARNAVIP</span> &mdash; use it at checkout when you book yourself in!</p>
      <div class="cta-actions">
        <a href="https://www.eventbrite.com/o/british-anaesthetic-recovery-nurses-association-113028693951" class="btn btn-coral" target="_blank" rel="noopener">Browse on Eventbrite</a>
      </div>
    </div>
  </section>
```

## 3. The commented event template on `index.html`

The booking button in the copy-me-per-event block read:

```html
      <a href="EVENTBRITE-LINK" target="_blank" rel="noopener" class="btn btn-teal">Book on Eventbrite</a>
```

It now points at the members area instead.

## 4. Two benefit lines, on `index.html` and `members.html`

Both said:

> Free access to every BARNA webinar, with your booking code in the members area

The booking code was the Eventbrite one, so that line was stale the moment
Eventbrite went. It now reads "joined straight from the members area".

## Still in the stylesheet

`.promo-code-line` and `.promo-code` in `css/style.css` are now unused but have
been left alone, so restoring the band above needs no CSS work.
