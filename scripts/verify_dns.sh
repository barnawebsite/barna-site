#!/usr/bin/env bash
# Verify the barna.co.uk zone against dns-snapshot-2026-09-02-final.txt
# Run after ANY 20i package or DNS operation. Exit 0 = all good, 1 = drift.
# Usage: scripts/verify_dns.sh [resolver]   (default 1.1.1.1)

R="${1:-1.1.1.1}"
FAIL=0
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=1; }

echo "barna.co.uk zone check via @$R  ($(date -u '+%Y-%m-%d %H:%M:%S UTC'))"
echo

# --- apex A: exactly the four GitHub Pages IPs ---
GH="185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153"
A=$(dig +short barna.co.uk A @"$R" | sort | tr '\n' ' ' | xargs)
if [ "$A" = "$(echo $GH | tr ' ' '\n' | sort | tr '\n' ' ' | xargs)" ]; then
  ok "apex A = four GitHub Pages IPs"
else
  bad "apex A is '$A' (expected: $GH)"
fi

# --- apex AAAA: must be absent (a 20i package adds one) ---
AAAA=$(dig +short barna.co.uk AAAA @"$R")
[ -z "$AAAA" ] && ok "apex AAAA absent" || bad "apex AAAA PRESENT: $(echo $AAAA | xargs)"

# --- wildcard: must be absent ---
W=$(dig +short "zz-wildcard-probe-$RANDOM.barna.co.uk" A @"$R")
[ -z "$W" ] && ok "no wildcard A record" || bad "WILDCARD A present -> $(echo $W | xargs)"
WA=$(dig +short "zz-wildcard-probe-$RANDOM.barna.co.uk" AAAA @"$R")
[ -z "$WA" ] && ok "no wildcard AAAA record" || bad "WILDCARD AAAA present -> $(echo $WA | xargs)"

# --- MX ---
MX=$(dig +short barna.co.uk MX @"$R" | xargs)
[ "$MX" = "10 mx.stackmail.com." ] && ok "MX = 10 mx.stackmail.com." || bad "MX is '$MX'"

# --- SPF: exactly one record, ending ~all ---
SPF=$(dig +short barna.co.uk TXT @"$R" | grep -c 'v=spf1')
SPFV=$(dig +short barna.co.uk TXT @"$R" | grep 'v=spf1')
if [ "$SPF" -ne 1 ]; then
  bad "expected exactly 1 SPF record, found $SPF"
elif echo "$SPFV" | grep -q '~all'; then
  ok "one SPF record, ends ~all"
else
  bad "SPF qualifier changed (expected ~all): $SPFV"
fi

# --- DKIM (mailbox, StackMail) ---
dig +short default._domainkey.barna.co.uk TXT @"$R" | grep -q 'v=DKIM1' \
  && ok "DKIM default._domainkey present" || bad "DKIM default._domainkey MISSING"

# --- DMARC ---
dig +short _dmarc.barna.co.uk TXT @"$R" | grep -q 'v=DMARC1' \
  && ok "DMARC _dmarc present" || bad "DMARC _dmarc MISSING"

# --- Memberstack / Resend ---
dig +short resend._domainkey.barna.co.uk TXT @"$R" | grep -q 'p=' \
  && ok "resend._domainkey present" || bad "resend._domainkey MISSING"
dig +short send.barna.co.uk MX @"$R" | grep -q amazonses \
  && ok "send.barna.co.uk MX present" || bad "send.barna.co.uk MX MISSING"

# --- www must stay a CNAME, never an A ---
dig +short www.barna.co.uk CNAME @"$R" | grep -q 'barnawebsite.github.io' \
  && ok "www CNAME -> barnawebsite.github.io" || bad "www CNAME wrong/missing"

# --- nothing may resolve to the old agency package ---
for l in "" www. mail. ftp.; do
  dig +short "${l}barna.co.uk" A @"$R" | grep -q '185.151.30.226' \
    && bad "${l}barna.co.uk points at OLD package 185.151.30.226"
done
ok "nothing resolves to old package 185.151.30.226"

# --- the site itself ---
echo
C=$(curl -s -o /dev/null -w '%{http_code} %{remote_ip}' -L --max-time 20 https://barna.co.uk)
case "$C" in
  "200 185.199."*) ok "https://barna.co.uk -> $C (GitHub Pages)" ;;
  "200 "*)         bad "https://barna.co.uk -> $C  (200 but NOT a GitHub IP)" ;;
  *)               bad "https://barna.co.uk -> $C" ;;
esac
CW=$(curl -s -o /dev/null -w '%{http_code} %{remote_ip}' -L --max-time 20 https://www.barna.co.uk)
case "$CW" in
  "200 185.199."*) ok "https://www.barna.co.uk -> $CW (GitHub Pages)" ;;
  *)               bad "https://www.barna.co.uk -> $CW" ;;
esac

echo
[ $FAIL -eq 0 ] && echo "RESULT: zone matches snapshot, site healthy." \
                || echo "RESULT: DRIFT DETECTED. Compare against dns-snapshot-2026-09-02-final.txt and restore at 20i."
exit $FAIL
