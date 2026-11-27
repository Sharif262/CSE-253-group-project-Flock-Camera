# Flock Agency Transparency Map — data (March and November 2026)

This folder holds the data behind the map. Each agency that has a Flock transparency portal is one dot. Its fill shows how much the portal discloses (0–6), its ring shows how many other U.S. states it lists as data recipients, and gray symbols mark agencies that can't be scored. The rules come from the project rubric (Flock Agency Transparency Map — Rubric).

## Files (data/)

| File | What it is |
|---|---|
| agencies.csv | **The map input.** One row per agency per snapshot: 2,542 rows, 1,651 agencies, 83 columns. |
| recipients.csv | Every name on each agency's "Organizations granted access" list, per snapshot (763,011 rows). Use it to recompute or inspect rings. |
| recipient_lookup.csv | The reviewed type and state for each of the 7,047 distinct recipient names. |

## How the data was created

**Sources (nothing else was used)**
- March 2026: the archived scrape of 897 portal URLs (one column per portal, one row per field label).
- November 2026: a scrape of 1,612 URLs (the 897 March URLs plus 715 candidates first seen in November), 1,759 fetch attempts with the saved page text and parsed fields.
- 26 November 2026: a rescrape of 165 URLs, 222 fetch attempts with the saved page text and parsed fields (see "Update: 26 November 2026 rescrape" below). It re-checked the 81 portals not found once, retried Harrison County OH and Lady Lake FL, and fetched 82 portals found only by Eyes on Flock (EyesOnFlock.com).
- uscities.csv (SimpleMaps) for positions.

**Steps**
1. **Agencies.** Flock's own portals (training, sales, marketing, admin and test) were dropped. agency_id is the portal slug without leading or trailing hyphens. The display name is the November page title (deactivation tags removed), or the name in the March sharing-list label if the portal is gone. The home state comes from the name, then the slug, else it was set by hand.
2. **Status** (one per agency per snapshot):
   - **Scored:** the portal fields were parsed.
   - **Inactive:** retention reads "-Infinity days" or "No devices currently live"; or the page shows a deactivation tag ([Inactive], [deactivated]) or notice; or it reports 0 cameras, 0 searches and 0 detections.
   - **Unassessable:** the fetch failed, the page was an empty shell, or the page showed only Flock's overview paragraph and was never retried.
   - **Removed:** Flock's "page not found" on two or more fetches (81 matched portals: 75 confirmed by the 26 November rescrape, 6 by a team member's manual check after the rescrape could not reach them).
   - **Retried overview-only pages:** pages that looked identical on a retry score 0 (nine pages: seven in the November scrape, plus Harrison County OH and Lady Lake FL on 26 November).
   - **Not-found portals:** a matched portal that showed Flock's "page not found" on only one fetch stays Unassessable with `not_found_once = 1`, because the rubric's Removed needs two not-found fetches. None remain. On the 6 portals confirmed Removed by a manual check, `not_found_once` stays 1: the scrapes saw the not-found page once, and the second result came from the manual check.
   - **New candidates:** the 36 that were not found are not drawn.
3. **Disclosure score (0–6).** One point each for:
   - a retention period for camera/LPR data
   - the agency's own camera count
   - a search count with its period
   - the public search-audit "Download CSV"
   - the "Organizations granted access" list (a statement that it shares with no one counts as a zero-recipient list)
   - the agency's own ALPR policy, named, linked or shown as text

   November fields were identified by Flock's fixed description text, March fields by label, and agency-written fields by label. A reported 0 counts; blank, "Data Unavailable", negative and infinite values don't.
   - Five custom-layout November pages were scored by hand from their saved text (Cedar Hill TX added on 26 November).
   - Fill bins: 6 dark blue (#2c7bb6), 5 light blue (#abd9e9), 4 orange (#fdae61), 0–3 red (#d7191c).
4. **Recipients.** March lists are comma-joined, so names split by their own commas were re-joined. Every distinct name was typed and placed in one lookup:
   - **Types:** state/local, federal (the project's federal list, including HIDTA), tribal, multi-state network, Flock/test, or stale.
   - **States:** resolved from state codes or names, applying the rubric's "SD"/"CO" and "LA" rules.
   - **By hand:** the remaining names were resolved using the states of the agencies that list them. Every "LA" name was reviewed and all of them are Louisiana.
   - **Counts:** 6,826 state/local, 136 stale, 27 tribal, 21 federal, 20 Flock/test, 12 multi-state and 5 unresolved.
5. **Rings.**
   - **Counting:** each ring counts other U.S. states (not DC) among the agency's state/local recipients.
   - **Other portals:** if another portal's "Receiving Network Data From" list names the agency (exact name match), that portal's state counts too.
   - **Classes:** none = 0 other states, thin = 1–19, thick = 20+.
   - **Dashed:** the agency publishes no list, so the states come only from other portals (a minimum).
   - **Gray:** no list and no out-of-state evidence.
   - **Federal badge:** at least one recipient is on the federal list.
6. **Positions.**
   - **City agencies:** at the uscities point.
   - **County agencies:** at the mean of the uscities places in that county. Independent cities are kept separate.
   - **Campuses:** at their host city.
   - **Towns and townships missing from uscities:** at a place inside them, or at their county centroid.

   Every position says how it was made in geocode_basis, and positions are identical in both snapshots.
7. **Change since March** (November rows of matched agencies, Scored in both, plus removed portals):
   - **What's compared:** fill band; ring class and federal badge only when the agency published its own list both times.
   - **List changes:** "newly disclosed" / "list hidden" mean the agency's own list appeared / disappeared.
   - **Result:** 303 agencies are flagged: 222 for a change in fill, ring or badge, and 81 removed portals.

**Checks**
- 17 structural checks pass. Among them:
  - score = sum of flags
  - non-Scored rows carry no score or ring
  - gray ring ⇔ no list and no evidence
  - one row per agency per snapshot
  - identical positions
  - every recipient is in the lookup
  - no text cell starts with = + - @ (so spreadsheets don't read it as a formula)
- An independent re-derivation of items 1–5 for every scored row, and random field-by-field audits against the raw scrape, found no unexplained differences.
- The policy item was spot-checked with 50 positives and 50 negatives per snapshot, as the rubric asks; the errors found were fixed.

**Cross-referenced with GPT.** The same rubric and raw data were also run through GPT, and the two results were compared row by row. Every disagreement was checked against the raw scrape:
- Where GPT was right, its finding was adopted. Examples: not-found portals as Unassessable, DC not counted as a state, and several policy and position fixes.
- Where the raw data contradicted it, this version was kept. Examples: "Grundy CO SO" is Grundy County, Illinois; three pages post deactivation notices; and every agency has a position.

## Column guide (agencies.csv)

- **Identity and position:** agency_id, name, state, agency_type, portal_url, lat, lon, geocode_basis.
- **Source and status:** snapshot (2026-03 or 2026-11), collected_at, source_file, evidence_sha256, status (Scored / Inactive / Removed / Unassessable), status_detail, cohort (matched = a March URL; new = first seen in November, not necessarily a new program), not_found_once.
- **Score:**
  - f_retention, f_cameras, f_searches, f_audit, f_sharing_list, f_policy (0/1); score (0–6); missing_features; fill_band (0-3, 4, 5, 6); fill_color.
  - For each item and for detections and hotlist hits (not scored): *_value, *_label, *_description, *_period_days.
  - sharing_list_value, policy_value, flag_data_unavailable, data_unavailable_fields, flag_no_live_devices.
- **Sharing:**
  - list_published, n_recipients (distinct names), other_states_low / other_states_high, other_states_list, other_states_label (text with "≥" where it is a minimum).
  - ring_class (none / thin / thick / gray), ring_source (own list / other portals), ring_dashed, ring_bounded (show "≥"), states_from_other_portals, other_portals_naming.
  - federal_flag, federal_names, n_multistate / multistate_names, n_tribal / tribal_names, n_flock_test / flock_test_names, n_stale, n_unresolved.
- **November only:** top_offense_types_present, inbound_list_present.
- **Change:** changed_since_march, change_summary, status_change.

**Blank values.** Inactive, Removed and Unassessable rows have no score, fill or ring. A blank federal_flag on a row with no own list means unknown, not "no federal sharing".

## Counts

| | March 2026 | Nov 2026, matched | Nov 2026, first seen |
|---|---:|---:|---:|
| Scored | 838 | 779 | 755 |
| Inactive | 21 | 28 | 4 |
| Removed | 0 | 81 | 0 |
|   of which confirmed by a manual check | 0 | 6 | 0 |
| Unassessable | 32 | 3 | 1 |
| Fill 6 (dark blue) | 47 | 62 | 60 |
| Fill 5 (light blue) | 314 | 293 | 339 |
| Fill 4 (orange) | 210 | 185 | 223 |
| Fill 0–3 (red) | 267 | 239 | 133 |
| Ring none | 280 | 333 | 272 |
| Ring thin (own list / dashed) | 104 / 140 | 70 / 55 | 104 / 60 |
| Ring thick (own list / dashed) | 146 / 0 | 95 / 65 | 146 / 50 |
| Ring gray | 168 | 161 | 123 |
| Federal badge | 176 | 116 | 167 |

## Update: 26 November 2026 rescrape (165 portals)

The team rescraped 165 portal URLs on 26 November 2026 (20:20–23:58 UTC) and processed them with the same rules and code as the rest of the data. Only these 165 agencies' November rows changed or were added; every other row in the three files is byte-for-byte unchanged and in its original order.

- **82 portals found only by Eyes on Flock** were added as new agencies (cohort "new", first seen in November; no March row). 81 had standard fields and were scored. Cedar Hill TX shows only an overview paragraph written by the agency and was scored 0 by hand (proposed, see below). Names come from the page titles. Positions come from eyes-on-flock/eof_only_portals.csv, which placed them with uscities.csv by the same rules: 14 sheriffs at county centroids and four New England towns missing from uscities at their county centroid (Beacon Falls CT, Braintree MA, Fairhaven MA, Medway MA).
- **81 portals not found once in November:** 75 showed Flock's not-found page again (41 of them twice that day), so they are now **Removed**. None came back. The other 6 (Boonsboro MD, South Tucson AZ, Stow MA, Sunset Valley TX, Taylor TX, Tewksbury MA) got an HTTP 429 and then a browser error, so the rescrape reached no page. A team member then checked them by hand (reported 27 November 2026) and all six showed Flock's not-found page, so they are Removed too. That decision is recorded in the pipeline's manual/status_overrides.csv; no page text was saved for the manual check.
- **Harrison County OH SO and Lady Lake FL PD** again showed only Flock's overview paragraph. Their November text, rebuilt and checked against its SHA-256 in agencies.csv, matches the 26 November text apart from the "Last updated" date and a header line the rescrape scraper captures on every page, so both score 0 under the retry rule (proposed, see below).
- **Recipients:** the 81 new published lists add 27,296 rows to recipients.csv and 7 new names to recipient_lookup.csv, all typed by rule (6 state/local, 1 multi-state network: Union Pacific - CA). "NM Department of Justice" is New Mexico's state department of justice, so state/local NM. n_lists grew for names already in the lookup; their type and state are unchanged.

**Checks.** All 17 structural checks pass. An independent run of the same task (GPT) produced identical scores, values, rings, positions, recipient rows and lookup entries for the 81 newly scored portals. Parsed values agree with Eyes on Flock's 12–13 November snapshots apart from expected drift (for example lists a few names longer or shorter).

**Proposed decisions, pending team review:** Harrison County OH and Lady Lake FL scored 0 (identical on retry); Cedar Hill TX hand-scored 0 (no retention, cameras, searches, audit download, list or named policy; fetched once); positions of the four New England towns. Berne IN is a borderline policy case: it rewrote Flock's template fields as detailed ALPR rules but names or links no policy, so it gets no policy point, as for earlier pages of this kind.

## Limitations and open items
- Everything here reflects what the portals declared at collection time. It is not a measure of actual sharing, searching or retention.
- March timestamps are month-only (2026-03). November rows carry the exact UTC collection time.
- **Rings of the agencies added or rescored on 26 November are a minimum.** They count states from their own lists and from the other rescraped portals' "Receiving Network Data From" lists. The existing portals' November lists were not re-read for them, so some gray rings could be dashed and some classes could be higher until the next full rebuild.
- **Rows outside the 165 were not changed**, even where a new portal's "Receiving Network Data From" list adds a state to their ring. A full rebuild would change 6: Ahoskie NC (thin to thick, dashed), Oconee County SC SO (thin to thick, dashed), Wolverine Lake MI (thin to thick, dashed), and Berlin CT, Newport RI and Westport CT (gray to thin, dashed).
- **March sharing fields captured as blank (24 Scored agencies).** These agencies had Flock's sharing field on the page with no names. The same agencies show the "not sharing data with any partner networks" statement in November, so they count as zero-recipient lists.
- **Unresolved recipients.** 5 names stay unresolved; they only affect the "≥" bound.
- **Approximate positions** are labelled in geocode_basis: county centroids, towns missing from uscities, campuses at their host city, and Mahoning Twp PA (county inferred).
