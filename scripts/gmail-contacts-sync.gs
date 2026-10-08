/**
 * BARNA Gmail contacts sync: the half that lives in Google Apps Script.
 *
 * Runs inside the barna.socialnetworks@gmail.com account (script.google.com),
 * deployed as a web app. Every morning scripts/sync_gmail_contacts.py, in the
 * GitHub expiry workflow, POSTs it the current member list read from
 * Memberstack, and this keeps two contact labels in step with it:
 *
 *   BARNA PAID MEMBERS  everyone with members-area access today
 *   BARNA EX MEMBERS    everyone whose access has ended
 *
 * It only ever adds contacts and moves them between those two labels. It never
 * deletes a contact, and never touches any other label (BARNA BOARD MEMBERS is
 * kept by hand). The Memberstack key stays on GitHub; this account only ever
 * sees names and email addresses.
 *
 * There is no password between the two halves: the web app's /exec address
 * is long and unguessable, and it is kept as the CONTACTS_SYNC_URL secret on
 * GitHub, never in the public repo. Anyone who could read it here can already
 * edit these contacts by hand, so a token in this file would protect nothing.
 * If the address ever leaks, make a new deployment and update the secret.
 *
 * Setup: paste this in, add the "People API" service (Services +), run
 * authorise() once and click Allow, then Deploy > New deployment > Web app,
 * execute as Me, access Anyone.
 */

var LABEL_ACTIVE = 'BARNA PAID MEMBERS';
var LABEL_PAST = 'BARNA EX MEMBERS';

/** Run once from the editor so Google asks for permission. Changes nothing. */
function authorise() {
  var groups = People.ContactGroups.list({ pageSize: 1000 }).contactGroups || [];
  Logger.log('OK, can see ' + groups.length + ' labels.');
}

function doPost(e) {
  var out;
  try {
    var body = JSON.parse(e.postData.contents);
    out = sync(body.members || [], body.live === true);
  } catch (err) {
    out = { ok: false, error: String(err) };
  }
  return ContentService.createTextOutput(JSON.stringify(out))
    .setMimeType(ContentService.MimeType.JSON);
}

function sync(members, live) {
  var active = {}, past = {};
  members.forEach(function (m) {
    var email = String(m.email || '').trim().toLowerCase();
    if (!email) return;
    (m.status === 'active' ? active : past)[email] = m;
  });
  // Someone active under one record beats a lapsed duplicate.
  Object.keys(active).forEach(function (e) { delete past[e]; });

  var activeGroup = groupFor(LABEL_ACTIVE, live);
  var pastGroup = groupFor(LABEL_PAST, live);

  // Index every contact by each of its email addresses.
  var byEmail = {}, pageToken;
  do {
    var page = People.People.Connections.list('people/me', {
      pageSize: 1000,
      personFields: 'names,emailAddresses,memberships',
      pageToken: pageToken
    });
    (page.connections || []).forEach(function (p) {
      var groups = (p.memberships || []).map(function (ms) {
        return ms.contactGroupMembership && ms.contactGroupMembership.contactGroupResourceName;
      });
      (p.emailAddresses || []).forEach(function (em) {
        var key = String(em.value || '').trim().toLowerCase();
        if (key && !byEmail[key]) byEmail[key] = { name: p.resourceName, groups: groups };
      });
    });
    pageToken = page.nextPageToken;
  } while (pageToken);

  var addActive = [], removeActive = [], addPast = [], removePast = [];
  var createActive = [], createPast = [];
  var report = { added: [], movedToPaid: [], movedToEx: [] };

  Object.keys(active).forEach(function (email) {
    var c = byEmail[email];
    if (!c) { createActive.push(active[email]); report.added.push(email + ' (paid)'); return; }
    if (c.groups.indexOf(activeGroup) < 0) { addActive.push(c.name); report.movedToPaid.push(email); }
    if (c.groups.indexOf(pastGroup) >= 0) removePast.push(c.name);
  });

  Object.keys(past).forEach(function (email) {
    var c = byEmail[email];
    if (!c) { createPast.push(past[email]); report.added.push(email + ' (ex)'); return; }
    if (c.groups.indexOf(activeGroup) >= 0) {
      removeActive.push(c.name);
      if (c.groups.indexOf(pastGroup) < 0) addPast.push(c.name);
      report.movedToEx.push(email);
    }
  });

  // Labelled paid but no longer a member under that address: move to ex.
  var seen = {};
  Object.keys(byEmail).forEach(function (email) {
    var c = byEmail[email];
    if (seen[c.name] || c.groups.indexOf(activeGroup) < 0) return;
    seen[c.name] = true;
    var stillActive = Object.keys(active).some(function (a) { return byEmail[a] && byEmail[a].name === c.name; });
    if (!stillActive && removeActive.indexOf(c.name) < 0) {
      removeActive.push(c.name);
      if (c.groups.indexOf(pastGroup) < 0) addPast.push(c.name);
      report.movedToEx.push(email + ' (not an active member)');
    }
  });

  if (live) {
    modify(activeGroup, addActive, removeActive);
    modify(pastGroup, addPast, removePast);
    create(createActive, activeGroup);
    create(createPast, pastGroup);
  }

  report.ok = true;
  report.live = live;
  report.activeMembers = Object.keys(active).length;
  report.pastMembers = Object.keys(past).length;
  return report;
}

function groupFor(label, live) {
  var groups = People.ContactGroups.list({ pageSize: 1000 }).contactGroups || [];
  for (var i = 0; i < groups.length; i++) {
    if (groups[i].name === label) return groups[i].resourceName;
  }
  if (!live) return 'contactGroups/NEW-' + label;
  return People.ContactGroups.create({ contactGroup: { name: label } }).resourceName;
}

function modify(group, add, remove) {
  for (var i = 0; i < Math.max(add.length, remove.length); i += 500) {
    People.ContactGroups.Members.modify(
      { resourceNamesToAdd: add.slice(i, i + 500), resourceNamesToRemove: remove.slice(i, i + 500) },
      group
    );
  }
}

function create(members, group) {
  for (var i = 0; i < members.length; i += 200) {
    var batch = members.slice(i, i + 200).map(function (m) {
      return { contactPerson: {
        names: [{ givenName: m.first || '', familyName: m.last || '' }],
        emailAddresses: [{ value: m.email }],
        memberships: [{ contactGroupMembership: { contactGroupResourceName: group } }]
      } };
    });
    People.People.batchCreateContacts({ contacts: batch, readMask: 'names' });
  }
}
