---
title: "Addendum: Nuevatel SAT Platform brief"
status: final
created: 2026-10-22
updated: 2026-10-30
---

# Addendum: Nuevatel SAT Platform

Supporting detail for downstream PRD and architecture work. It contains **no key material**: keys are referred to only by type and custody.

Source tags on facts added 2026-10-30: **[DOC]** document; **[LLAVE]** LLAVE's answer of 2026-10-30; **[INFERENCE]** untested inference. **Nothing has been validated on a real SIM yet.** Architecture changes from this update are marked PROPOSED.

## A. SIM profiles (technical summary)

### Profile 15.03

Source: `GE_GSM_NTE_15.03_S1178753`, dated 2022-06-10 [DOC].

- OS family USimera Prime; Java Card 3.0.1; GlobalPlatform 2.2; USIM / ISIM / CSIM; BIP; Admin Agent and DNS Resolver (SCP81 support) [DOC].
- Browser: Service Engine 5.01, menu "SAT Browser", instance AID ending in 534054. Push: Service Engine PUSH, instance AID ending in 505348 [DOC].
- Other applets: IMEI_Tracking, Utilities, TPD, SmartRoaming, SIMChronize_02, AutoProm, Generic 2G Phonebook Lookup, AppBooster 1.0.4, S@T SMS AdBanner 1.0.0, mta, S1159961A_Middleware, DNS Resolver, MultiRefresh, Polling [DOC].
- **Correction (2026-10-30):** "S@T Browser (SBT)" was wrong. The instance with AID ending in 53425401 is listed as Billing [DOC].
- The profile's description string lists WIB, but its applications list has no WIB instance [DOC]. Whether a WIB browser is present is unconfirmed.
- **AppBooster is not Sleepy.** Sleepy is a separate Mobiera applet installed after issuance (section K).
- The USIM/GSM file tree was reviewed. The network keys it holds (e.g. Kc) are unrelated to OTA keys and out of scope.

### OTA applications on 15.03

| Application | TAR | MSL (parameter / data) | Note |
|---|---|---|---|
| RAM | 000000 | 01 / 02 | |
| USIM_RFM | B00001 | 01 / 02 | |
| SIM_RFM | B00010 | 01 / 02 | |
| Service Engine (browser) | 534054 | **Not declared** [DOC] | No explicit TAR in the install block; TAR matches the AID suffix and S@T 01.50 [DOC]. Whether the card applies this TAR is untested |
| Service Engine PUSH | 505348 ("PSH") | **Not declared** [DOC] | Same as above |
| Admin Agent (SCP81) | B20100 | 01 / 02 | [DOC] |
| Sleepy (installed post-issuance) | 534C59 ("SLY") | 0 (see K) | Not in the profile |

Correction recorded 2026-10-28: TAR B00010 is SIM_RFM, not the S@T Browser. The exact meaning of MSL parameter 01 / data 02 on this profile is still unconfirmed and must be checked against the manufacturer's specification before the engine design is settled (OQ-6).

### Keysets (by type and custody only)

| Keyset | Contents (type) | Owner / platform relevance |
|---|---|---|
| 01 | OTA keys KIC, KID, KIK; ADM1 | KIC/KID/KIK in scope (SCP80 OTA, key service). ADM1 goes to the support vault, not the platform |
| 03 | ADM3, KIK, ISD_TLS_PSK | In scope for SCP81 (PSK-TLS). ADM3 goes to the support vault |
| 10 | Network authentication (Ki, OPc); the profile also lists a KIK entry here [DOC] | **Out of scope**: stays in the HSS |

KIC, KID and KIK have Algo ID 0x80 and 16 bytes; `algoNumber=3` appears in `.sec.xml`. Neither is decoded (OQ-20) [DOC]. The profile defines KID and KIK as separate variables [DOC], so KID = KIK on NTE04570 (section O) is not a property of the profile itself.

Custody status:

- OTA keys are unique per card and are delivered by the manufacturer as output files per lot. They cannot be reused across cards or lots. Many lots exist, past and current. Only NTE04570 is in the folder [DOC].
- Aircast keeps a copy of the keys in an AES-encrypted database in Nuevatel's datacenter. People operating that database or its server have no access to the OTA keys [DOC: IS-SU-TS 23915 §3.1]. The Aircast UI does not allow downloading user databases [DOC: §3.2.1]; the document describes no key export, so export is not assumed [INFERENCE].
- Output files are uploaded through the Operator UI, a Nuevatel-facing interface [DOC: §3.2.2], so Nuevatel should have held those files [INFERENCE] (OQ-26).
- Whether the keys are derived from a master key is unknown (OQ-5). If they are, whoever holds that master key is the strategic dependency.
- The contract-level and technical details of custody are partly unknown (OQ-7).
- The existing output files are stored in plaintext in a cloud-synced folder. They must be remediated first (OQ-10).

### Profile 15.05

Source: `NUBO0001.01_01280103_230317_15.05_USIM` [DOC].

- It describes files only; it has no applet or key section.
- It includes EF S@T Exchange (2F80), with SST 26/27/29 and UST 28 active.
- Its 785 OTA file rules state "Counter higher", with keyset version 1.
- These rules cover file access. They say nothing about RAM or applet TARs, or about whether a card shares one counter across TARs [INFERENCE].
## B. Aircast capabilities that must be replaced or reproduced

- Northbound REST API: UstkRequest of type Text, Menu, Url, Call or Ussd. The Nuevatel unified send API stays compatible with it (I, ADR-1). Consumers: a web page for mass campaigns by CSV, and VAS applications for purchases, reconnections and top-ups [LLAVE].
- SMSC connection over SMPP: an Aircast SMPP client connects to Nuevatel's SMSC [DOC: IS-SU-TS 23915 §2.1.3]. The SAT PUSH application connects directly, without the SMS firewall [LLAVE]; whether this means Aircast is OQ-28.
- Discovery: identifies each SIM's browser type through MO shortcodes, using a daily subscriber file as input (see F and Q).
- OTA bytecode generation for RAM, RFM, S@T, Sleepy, WIB and Pico.
- Per-card storage of keys and anti-replay counters.

## C. Migration approach

1. Nuevatel orchestration calls a unified send API compatible with UstkRequest.
2. At first the Aircast driver serves every send.
3. The Nuevatel OTA engine is built in parallel and validated in the lab, per SIM family.
4. The web campaign page and the VAS applications move to the unified API before Phase 6 (PROPOSED; OQ-30). They keep the request shape and change their endpoint.
5. SIM families move to the Nuevatel driver one at a time, with rollback. A per-ICCID flag ensures that only one platform operates a SIM at a time, for the traffic that passes through the unified API (I, ADR-3).

Preconditions: contracted access to the Aircast API for the transition (OQ-7); a counter route, either export per ICCID or a lab-proven jump in counter-higher families (OQ-4, OQ-33); key coverage for the target families (OQ-1, OQ-2).

## D. Phase detail

| Phase | Key activities | Exit / blocker |
|---|---|---|
| 0. Diagnosis | Remediate plaintext output files (including version history, recycle bin, backups, synced devices) and establish who had access (OQ-25); per-lot coverage audit (aggregates only, with no key values in reports; every opening of a secret file is logged, OQ-25); key-validity check; Aircast counter-export test on sample ICCIDs; Mobiera contract review; SMSC TPS and firewall review; skills assessment; follow up the manufacturer request; start HSM procurement. **New:** scoped sniffer on Aircast's SMPP bind (test lines only, with authorization and later deletion; it does not yield the Sleepy key); count of SIMs per profile and applet from Aircast; full snapshot of the base to measure OQ-1; lab test with an NTE04570 SIM (RFM read, and push to TARs 505348 and 534054 with and without security) | Gate: feasibility conditions 2–4 (documentation, Sleepy decision, coverage) plus a counter route (export or jump test), skills decision, owner, business case, and the Phase 5/6 fallback. The NTE04570 test is a single-lot probe and does not satisfy condition 1; it uses only the test SIMs' keys, under dual control and outside the repository |
| 1. Inventory and orchestration | Campaigns, ICCID-keyed inventory, Discovery (including S@T environment variables, L, and the dawn policy, Q), content | — |
| 2. Unified send API + Aircast driver | UstkRequest-compatible API; Aircast driver; callbacks and reporting; start moving the web page and VAS applications (PROPOSED) | Pivot checkpoint: S@T lab result and counter route re-checked; fallback applied if open |
| 3. Key service | HSM (model chosen after OQ-16/OQ-20), custody, counters, import, rotation design, governance (N) | Starts after the Phase 0 gate |
| 4. Lab and minimal OTA engine | Card readers, test SIMs per family, handset matrix (including iPhone); SCP80 engine able to perform an RFM read; counter validation mode confirmed per family | Starts after the Phase 0 gate. Feasibility condition 1: real RFM read with positive proof of receipt, per SIM family. Rotate lots with confirmed plaintext exposure after this phase |
| 5. S@T push and menu | S@T push; menu cleanup and new menus | **Unblocked on paper**: TAR and S@T specifications in hand (OQ-6, OQ-23) [DOC]. Needs a lab proof per family; MSL meaning open. Families that fail stay on the Aircast driver |
| 6. Migration by SIM family | Counter import or jump, per-ICCID ownership switch, per-family cutover with rollback; Aircast decommission criteria | **Blocked** until counters can be exported or a counter jump is proven per family (OQ-4), and until the web page and VAS applications have moved (OQ-30). A jump without a proven rollback to Aircast is a one-way cutover, approved explicitly per family (OQ-33) |
| 7. Full independence | Nuevatel applet loaded via RAM or SCP81 (replacing Sleepy); rotation to Nuevatel-controlled keys | Gated by a lab spike on new-lot samples (R8). SCP81 is blocked on NTE04570 without the PSK [DOC] |

## E. Request to the SIM manufacturer (new lot ordered 2026-10-22)

A formal request was prepared. It covers:

- Key custody, including whether keys are derived from a master key.
- Separate, encrypted output files.
- Algorithms, TAR and MSL specifications.
- Counter policy.
- SCP81 PSK.
- The applet list.
- Lab samples.
- Escrow.
- Terms for future contracts.

**To add before the 2026-10-22 lot is produced (2026-10-30):**

- MSL with CC and counter for S@T and PUSH.
- KID different from KIK.
- Counter mode and algorithm.
- The PSK.
- The meaning of securityID.
- Ownership of Satpush v2.0 and its relation to 15.05.

The answers feed OQ-1, OQ-2, OQ-4, OQ-5, OQ-6, OQ-20, OQ-22 and OQ-31 directly. Whether the request has been sent, who the lot's manufacturer is and whether production has started are OQ-15.

## F. Test-matrix inputs

The known defects listed in the brief each need a lab test case: per SIM family for the Idemia S@T auto-accept issue, per handset for iPhone S@T, menu-entry checks for the dead entries, and ICCID-keyed reconciliation tests for the Discovery feed (IMSI vs ICCID mismatches). Every family also needs the condition-1 test: a real RFM read with a positive proof of receipt.

`docs/Perfil eléctrico VIVA.xlsx` is a map of the SIM menu, not an electrical profile. It lists the entries that fail, loop or show "Service unavailable" [DOC], and is an input for the menu checks. The S@T lab cases cover both TARs, because the unsecured-push exposure in R11 applies to 534054 as well as PSH [INFERENCE].

## G. Legacy assets

- An old in-house Java SATClient library. Its reusability has not been assessed.
- Gemalto LinqUs Push Manager 5.1 documentation, as a reference design for a push manager.

## H. Pre-mortem (2026-10-22)

Phase numbers in the narrative below refer to the roadmap as it stood on 2026-10-22; the risk register at the end of this section uses the current roadmap.

**Premise.** It is April 2028 and the SAT Platform is considered a failure. This is a hypothetical narrative, not a forecast.

**The failure story.** The orchestrator went live on Aircast and campaigns moved over. But the Phase 0 audit was rushed. The SCP80 pilot then showed that many older lots had output files that were missing, outdated or derived from a manufacturer master key. Aircast held the counters, and with no current contract there was no lever to make Mobiera export them, so the first in-house sends to existing SIMs were rejected. The team kept both systems running. The one engineer who understood the OTA cryptography left. The HSM was still in procurement. A mis-targeted menu push reached a large segment without a canary stage and drew complaints. With no visible subscriber benefit and double running cost, the budget was not renewed.

**Causes, mapped to the brief's risk table:** diagnosis treated as paperwork (R1); commercial leverage over Aircast never secured (R2); API shaped by Aircast (R3); single points of failure in people and procurement (R4); no blast-radius controls (R5); one pilot overall instead of one per family (R6); value delivered too late (R7); applet replacement assumed rather than tested (R8); no exit criteria for Aircast (R9).

**Ideas considered but not added to the brief:**

- *Freeze new SIM-based services until migration.* Rejected because it worsens R7.
- *Replace SIMs on unreachable lots.* Kept only as a per-family option, because its cost and logistics are unknown.

### Second pre-mortem (2026-10-28)

**Premise.** It is October 2028 and the platform has stalled. Hypothetical, not a forecast.

**The story.** Phases 1–4 shipped; an RFM read with proof of receipt worked on two SIM families. Phase 5 never began because the TCA companion specifications were never obtained, and Phase 6 never began because Mobiera agreed in principle to export counters but never delivered. All production traffic still ran through the Aircast driver: Nuevatel had built a polished UstkRequest front end for Aircast. On the new lot the cards turned out to require exactly-plus-one counters, so every lost SMS left a card "uncertain" with no recovery. The HSM chosen in Phase 0 lacked the mode the manufacturer finally documented. An audit found old plaintext output files in the cloud folder's version history, and rotation sat in Phase 7. An Aircast campaign from another consumer reached migrated SIMs because Aircast never read the per-ICCID flag.

| # | Cause | Early warning | Change applied |
|---|---|---|---|
| P1 | Blocked at the finish line: Phases 5–6 depend on parties who never deliver | OQ-23 and counter export still open at the end of Phase 2 | Fallback decided at the Phase 0 gate; pivot checkpoint after Phase 2; R13 |
| P2 | Unrecoverable counters under exactly-plus-one | Counter mode not confirmed in the lab before the pilot | Lab confirms counter mode per family (condition 1); OQ-24 |
| P3 | HSM chosen before the algorithms are known | Purchase decided before the manufacturer answers | Procurement starts in Phase 0; model chosen after OQ-16/OQ-20 (Decision 5) |
| P4 | Rotation too late for possibly exposed keys | Plaintext audit finds copies or unexpected access | Remediation covers version history, recycle bin, backups, synced devices; OQ-25; rotate exposed lots after Phase 4 |
| P5 | Per-ICCID flag does not bind Aircast | Aircast SMPP bypasses the Nuevatel gateway | *Superseded 2026-10-30.* Was: route Aircast SMPP through the Nuevatel exit gate. Now (PROPOSED): no edge enforcement; move the web page and VAS applications to the unified API before Phase 6, and exclude migrated SIMs from Aircast's own senders (ADR-3, OQ-30, OQ-34) |
| P6 | Firewall cannot filter what R11 needs | Firewall cannot inspect the TAR; external PID 0x7F not blocked | *Revised 2026-10-30.* The firewall's role narrows to blocking external PID 0x7F (OQ-8, OQ-28); exposure sized via OQ-3 and OQ-27 |
| P7 | Spending ahead of the gate | Phase 3 spend before the Phase 0 gate | Phases 1–2 start now; Phases 3–4 wait for the gate |

### Risk register (current roadmap, updated 2026-10-30)

Full table; the brief keeps only the five risks that gate the program.

| # | How it fails | Early warning | Mitigation now |
|---|---|---|---|
| R1 | **Unreachable base.** Most active SIMs lack valid output files, so the engine reaches only new lots and Aircast can never be retired (OQ-1, OQ-2, OQ-5). | Phase 0 coverage below threshold | Coverage is a Phase 0 gate criterion. Plan per family: in-house, stay on Aircast, or retire through SIM replacement. G4 and G7 measured on the reachable segment. |
| R2 | **Counters and keys locked in Aircast.** Mobiera does not cooperate, so the first in-house sends are rejected as replays (OQ-4, OQ-7). | No export on sample ICCIDs and no passed jump test by the Phase 0 gate | Secure access and export rights at the Phase 0 gate. Test export on sample ICCIDs. Confirm the counter validation mode (OQ-4). [INFERENCE, needs a lab test] In counter-higher families, export may be unnecessary if the engine starts above anything Aircast used, with a single sender per SIM. 15.03 is unconfirmed. The only counter-higher evidence is from 15.05 file rules, and no 15.05 lot keys are in the folder. A jump is a one-way cutover per family unless the lab proves a rollback to Aircast (OQ-33). |
| R3 | **Send API shaped by Aircast.** The UstkRequest-compatible contract cannot express what the Nuevatel engine needs (RAM/RFM, S@T push, SCP81). | An engine feature requires a contract change | Accepted trade-off. Keep orchestration independent of the driver; extend the contract in a versioned way. |
| R4 | **Skills and long-lead items.** OTA cryptography and HSM knowledge sit with one person; HSM procurement stalls Phase 3 (OQ-9, OQ-16). | No build, hire or partner decision at the Phase 0 gate | Decision is a gate criterion. Start HSM procurement in Phase 0. Two people per critical skill. |
| R5 | **Field incident.** A wrong mass send or a bad RFM write harms subscribers, draws ATT attention, and leadership halts the program (OQ-13). | Mass sends without canary or dual control | Per-campaign volume limits, canary then ramp, dual control, emergency stop, pre-tested rollback; consult ATT before the first mass campaign. |
| R6 | **Fragmentation.** It works in the lab but fails on real handsets and SIM families (iPhone, Idemia auto-accept) (OQ-17). | Results differ by family or handset | Lab validation per SIM family; handset matrix from the real device mix. |
| R7 | **No visible value.** Long plumbing, no change for subscribers, and the budget is cut (OQ-11, OQ-12). | No business owner or business case at the Phase 0 gate | Owner and business case are gate criteria; an early visible win via the Aircast driver; G8. |
| R8 | **Applet infeasible on old lots.** Loading a Nuevatel applet needs privileges only the manufacturer holds, so Sleepy stays (OQ-3, OQ-5). | Lab spike fails on samples | Treat Phase 7 as an option, gated by a lab spike on new-lot samples. |
| R9 | **Zombie migration.** Aircast and the new platform run side by side indefinitely, at double cost. | No decommission date after the pilot | Define decommission criteria before Phase 6 starts. |
| R10 | **Counter divergence.** Both platforms send to the same cards, so the cards reject packets as replays. | Any card receiving OTA from both | Per-ICCID ownership flag; single sender per card; counter export or jump at cutover. The flag binds only unified-API traffic: move the web page and VAS applications first (OQ-30), and exclude migrated SIMs from Aircast's own senders (OQ-34). |
| R11 | **Unsecured push reachable by third parties.** *Sleepy*: at MSL 0, anyone able to send SMS-PP to TAR "SLY" reaches the applet. Sized at the worst case, the whole base, until OQ-27 is answered. *S@T (added 2026-10-30)*: browsers must support SPI 0x0000 (S@T 01.50 §5.5.2); 15.03 declares no MSL for Service Engine or PUSH; with no MSL at install, no minimum security is required (SIMalliance guide §9.7) [DOC]. A Simjacker-type push is therefore possible [INFERENCE, to be tested]. | OTA-class SMS from unauthorized origins; the lab accepts an unsecured push | SMS firewall blocks external PID 0x7F (OQ-8, OQ-28). Phase 0 lab test of both S@T TARs, with and without security. MSL with CC and counter on the new lot (E). The remedy for the installed base is open. |
| R12 | **S@T push stalls.** *Revised 2026-10-30*: the specification gap is closed on paper (OQ-23) [DOC], but the specifications do not prove how each browser family behaves, and known S@T defects exist on Idemia and iPhone. | Lab push fails on a family; 3GPP TS 23.048 or ETSI TS 102 225/226 still missing when the lab test starts | Lab proof per family; failing families stay on the Aircast driver; obtain the remaining standards. |
| R13 | **Blocked at the finish line.** Phases 1–4 deliver but Phases 5 and 6 wait on lab proofs or external parties, leaving Nuevatel more dependent on Aircast. | S@T lab proof or a counter route (export or jump) still open at the end of Phase 2 | Fallback decided at the Phase 0 gate; pivot checkpoint after Phase 2. |
| R14 | **KID = KIK.** The two keys are identical on all 10,000 NTE04570 cards [DOC]. Whoever can use one holds the other, and rotation via KIK gives less isolation [INFERENCE]. It may be an export artifact rather than the card state [INFERENCE]. | Lab or manufacturer confirms the equality on the cards | Ask the manufacturer (E); require KID ≠ KIK on the new lot; confirm the card state in the lab; account for it in the rotation design (N). |
| R15 | **Identifiers outside `.gitignore`.** `docs/NTE04570.card.xml` holds 10,000 IMSIs and serials [DOC]. `.gitignore` covers `.OUT` and `.sec.xml` only, and `docs/` is untracked (checked with `git check-ignore` on 2026-10-30), so `git add docs/` would commit subscriber identifiers. | The file appears in `git status` as addable, or in any commit | Extend `.gitignore`; include the file in the Phase 0 remediation (OQ-10, OQ-25). |

## I. Architecture decision records (proposed)

Inputs to `bmad-architecture`, not final decisions.

| ADR | Options considered | Trade-offs | Proposed |
|---|---|---|---|
| 1. Send API (revised 2026-10-28; reinforced 2026-10-30) | (a) UstkRequest-compatible unified send API with two drivers. (b) Nuevatel domain API with an Aircast adapter. (c) Events only. | (a) keeps the existing consumers' request shape and makes the driver swap invisible, but ties the contract to Aircast's request shape (R3). (b) was the 2026-10-22 proposal. (c) does not fit synchronous menu pushes. | **(a)**, per the functional architecture. Extend the contract in a versioned way when the engine needs more than UstkRequest expresses. The known consumers, a CSV campaign web page and VAS applications for purchases, reconnections and top-ups [LLAVE], reinforce compatibility: they change only their endpoint (ADR-3). |
| 2. Crypto boundary | (a) Keys encrypted in the application database. (b) HSM releases keys at runtime. (c) Operations run inside the HSM; per-card keys stored only wrapped under the HSM master key. | (a) and (b) expose keys in application memory. (c) needs HSM support for the profiles' algorithms, possibly 3DES (OQ-16, OQ-20). | **(c)**. Separate keys per environment; the engine never sees master keys. |
| 3. Counter ownership in coexistence (revised 2026-10-30, PROPOSED) | (a) Both systems send to any card. (b) Single sender per card, switched by a per-ICCID flag, with Aircast's counters exported at cutover or jumped in counter-higher families. | (a) makes counters diverge and cards reject packets (R10). (b) needs the flag plus the export or a lab-proven jump. If Aircast goes directly to the SMSC (OQ-28) and its consumers call its API (OQ-19), the flag cannot be enforced at the edge. | **(b)**. A hard rule for Phases 4–6. Move the web page and VAS applications to the unified API before Phase 6 (OQ-30). Aircast's own senders must exclude migrated SIMs (OQ-34). |
| 4. OTA engine sourcing | (a) Build in-house. (b) Buy another vendor's engine. (c) Partner for the crypto core; build the rest. | (b) swaps one dependency for another. (c) reduces skills risk (R4) if keys stay in Nuevatel's HSM. | **(a)**; (c) as fallback at the Phase 0 skills gate; (b) rejected. |
| 5. SMSC integration (revised 2026-10-30, PROPOSED) | (a) Shared SMPP binds. (b) Dedicated OTA bind behind a single exit gate, with Aircast also routed through it (2026-10-28 proposal). (c) Own traffic directly to the SMSC over a dedicated bind, with the firewall only blocking external PID 0x7F. | (a) cannot enforce OTA throttling. (b) contradicts the direct path reported by LLAVE [LLAVE] and would require re-routing Aircast. (c) matches today's topology and keeps volume limits and the emergency stop enforceable on own traffic, but gives no edge control over Aircast (ADR-3). | **(c)**. Bind restricted by IP and system_id, with a TPS limit and an emergency stop. Throughput budget depends on OQ-8. Firewall behavior depends on OQ-28. |
| 6. Inventory identity (revised 2026-10-30, PROPOSED) | (a) IMSI-keyed, fed by the daily file. (b) ICCID-keyed, with the IMSI mapping from the authoritative source. | (a) keeps today's Discovery mismatches. (b) addresses the root cause; S@T environment variables can supply ICCID directly (L). | **(b)**. Source = a direct CRM extract [LLAVE], with prior validation against lot NTE04570, which covers only its own 10,000 SIMs. The daily report does not count as a source until validated, since that feed produced the earlier mismatches [DOC] (OQ-29). The parser must handle ICCID at 20 characters in `.OUT` and 18 digits in `.sec.xml` [DOC]. |

## J. Contract context

The prior Mobiera contract expired in July 2022 (OQ-7). The July 2022 email ("no dependency; Nuevatel keeps keys and control") conflicts with the Sleepy key and specification being held only by Mobiera, and with the anti-replay counters being held in Aircast (Mobiera software, hosted in Nuevatel's datacenter). Legal review is needed.

In March 2026 Mobiera was still requesting IMSI ranges to prepare the Aircast database for Discovery and SAT PUSH campaigns used by Marketing [DOC]. This signals an active relationship [INFERENCE], whose contractual basis is unknown.

## K. Sleepy applet (Mobiera guide v9, January 2023)

- Package AID prefix 4D4F42434F ("MOBCO"); TAR 534C59 ("SLY").
- Requires Java Card 2.2.1 and the ETSI UICC/USIM APIs.
- About 8.6 KB of code and up to about 6.7 KB of NVRAM.
- Installed after issuance, with minimum security level 0, because it applies its own proprietary security. The guide does not document that security (key, algorithm, command format). IS-SU-TS 23915 §3.3 adds that it is application-level AES or 3DES, independent of the OTA keys [DOC]; the key and command format remain undocumented.
- Its validation message uses PID 0x7F, DCS 0xF6 and ESM class 0x40.

**Evidence added 2026-10-30.**

- Reach: installed on all SIMs [LLAVE]. Documents point the other way: Aircast would install Sleepy on SIMs with a defective engine (IS-SU-TS 23915 §1), the API reaches SIMs regardless of the push engine installed (§3.4), and Discovery exists to identify the browser on each SIM (§2.1.7) [DOC]. Unresolved (OQ-27).
- G+D thread, June 2023: SMS to TAR SLY with SPI 00 00 and applet versions 07.00 and 07.01; tests were still not closed on 2023-06-20, with SMS arriving without content in roaming [DOC]. Mobiera says the applet is on Nuevatel's eSIM in that thread [DOC] (OQ-32).
- LLAVE suggests a sniffer on current SAT PUSH traffic [LLAVE]. It can show formats and volumes on test lines, but does not yield the Sleepy key.

**Implications.**

- The OTA keys (KIC/KID/KIK) are not enough to operate Sleepy. Its specification and key remain a Mobiera dependency (OQ-3).
- With MSL 0, any party able to send SMS-PP to TAR "SLY" reaches the applet. The firewall must block external PID 0x7F (R11, OQ-28).
- Feasibility condition 3: obtain the specification and key, replace Sleepy with a Nuevatel applet (Phase 7), or use S@T where it works [INFERENCE]. Sleepy was proposed for SIMs whose engine is defective [DOC], so S@T may not work on exactly those SIMs [INFERENCE]. Using S@T also leaves the applet on the card, so R11 stays.

## L. S@T specifications (SIMalliance, v4.0.0, Release 2009)

**In the folder [DOC]** (OQ-23 resolved):

| Document | Title |
|---|---|
| S@T 01.00 | SBC (bytecode): decks, cards, commands; a secure message (3DES, 8-byte MAC, SPI 0x02 / 0x04 / 0x06); environment variables (ICCID, browser supplier, browser version, profile, buffer size) |
| S@T 01.10 | S@T Markup Language (S@TML) |
| S@T 01.20 | Session Protocol |
| S@T 01.21 | Administrative Commands |
| S@T 01.22 | Operational Commands (pull protocol) |
| S@T 01.23 | Push Commands |
| S@T 01.50 | Browser Behavior Guidelines |

**Key facts [DOC].**

- S@T 01.50 §5.5.1: Pull, Administration and High Priority Push use TAR 534054; Low Priority Push uses TAR 505348 ("PSH"). This resolves the TAR part of OQ-6. The MSL 01/02 part stays open.
- S@T 01.50 §5.5.2: the browser must support SPI 0x0000 (no security) and SPI 0x1200 (3DES cryptographic checksum, counter higher).
- SIMalliance guide "Interoperability Stepping Stones" (2004) §9.7: if no MSL is specified at installation, no minimum security is required.
- `Ejemplo S@T Push.txt`: tag 0x42 with no 23.048 header, and a Portuguese message from "CORREIOS CELULAR". It does not prove the security level, and its origin is not stated.

**Opportunity**: a deck can read the environment variables, so Nuevatel can build its own SIM inventory without Mobiera's Discovery.

**Remaining gap**: 3GPP TS 23.048 and ETSI TS 102 225 / 102 226 are still outside the folder [DOC]. The specifications do not prove that Service Engine 5.01 behaves as specified (R12).

## M. Functional architecture (proposed)

**Sources**

- OCS/BSS: balance and top-up events.
- CRM: audiences, and the ICCID-to-IMSI mapping [LLAVE].
- HLR/HSS: IMSI/IMEI changes, SIM swap.
- Operator UI.

**Nuevatel platform**

- Orchestration: campaigns, inventory, Discovery, content.
- Unified send API, compatible with Aircast's UstkRequest.
- Two drivers behind it:
  - Aircast driver (transitional).
  - Nuevatel OTA engine: SCP80 with RAM/RFM and S@T first; SCP81 later.
- Key service, used only by the OTA engine.

**Outbound path (PROPOSED, revised 2026-10-30)**

Dedicated SMPP bind directly to the SMSC (restricted by IP and system_id, with a TPS limit and an emergency stop) → network → handset → SIM applets addressed by TAR (tables in A; S@T protocols per TAR in L).

Own traffic does not cross the SMS firewall [LLAVE]. The firewall stays only to block external PID 0x7F (OQ-28). Aircast's traffic is not routed through Nuevatel; its path is OQ-28.

**Return path**

Proofs of receipt and MO messages → SMSC → engine → callbacks and KPIs.

**Design rules**

- A dedicated bind for own traffic, not a shared exit gate. The per-ICCID flag binds only unified-API traffic (I, ADR-3).
- The engine never sees master keys.
- Counters are reserved transactionally before sending.

## N. Key service (proposed)

**Custody**

- Per-card KIC/KID/KIK, stored wrapped under an HSM master key.
- The platform never stores Ki, OPc, PIN, PUK or ADM. Ki/OPc go to the HSS; PIN, PUK and ADM go to a support vault.

**HSM**

- Cryptographic operations run inside the HSM.
- Verify 3DES support, which the cards may require (OQ-16).
- At least two HSMs.
- Split custody of the master key.

**Counters**

- Atomic reservation per card, with the states reserved → sent → confirmed, or uncertain.
- A single sender per card; a strongly consistent store.
- The validation mode (greater-than vs exactly-plus-one) drives the design. 15.05 file rules state "Counter higher" [DOC]; 15.03 is unconfirmed (OQ-4).
- Migration from Aircast needs a per-ICCID flag, so only one platform operates a SIM at a time, plus an export of Aircast's counters or, in counter-higher families, a counter jump.
- Counter jump [INFERENCE, needs a lab test]: start above anything Aircast used, with a single sender per SIM. Open points: how large a margin is safe without knowing Aircast's values, and whether the counter is shared across TARs. Without a lab-proven rollback to Aircast, the jump is a one-way cutover per family, approved explicitly at cutover (OQ-33).
- Confirm the validation mode per SIM family in the lab before any pilot. Under exactly-plus-one, a lost message leaves the card "uncertain"; a resynchronization procedure is needed before production (OQ-24).

**Rotation** (uses the KIK; the command the cards accept is OQ-22; KID = KIK on NTE04570 weakens it, R14)

1. Generate new keys and store them as pending.
2. Test in the lab.
3. Send a real validation message.
4. Activate in waves, with a stop condition.
5. Retire the old version only after stability.

**Import of output files**

- A parser per SIM family, including the ICCID length difference between `.OUT` and `.sec.xml` (O).
- Count and uniqueness checks.
- Two-person approval.
- Split into three destinations (by the custody rule above: OTA keys to the key service, Ki/OPc to the HSS, PIN/PUK/ADM to the support vault).
- Record a hash of each file; securely delete copies.
- The import report contains no key values.

**Governance**

- Separate keys per environment.
- Dual control.
- An immutable audit log.
- Mutual authentication between services.
- Volume limits per campaign.
- An emergency stop switch.

**Strategic note.** If the manufacturer derives per-card keys from a master key (OQ-5), whoever holds that master key controls the estate. The request for the new lot (E) asks about this, about escrow and about separate encrypted output files.

## O. Lot NTE04570 (aggregates only, no key values)

Facts supplied by the owner on 2026-10-30. The key files were not opened for this update.

- Header: "Manufacturer: VALID", profile 15.03, dated 27.01.25; profileName 15.03_VA. This is the only explicit link to Valid: `docs/Valid` does not name Valid in its content. To be confirmed with Valid [DOC].
- 10,000 SIMs with KIC, KID and KIK per card, unique per card. `.OUT` and `.sec.xml` match on all 10,000. Validity untested [DOC] (OQ-2).
- **Anomaly**: KID = KIK on all 10,000 cards [DOC] (R14).
- securityID is identical on all 10,000 cards; its meaning is unknown [DOC] (E).
- The file does not include ISD_TLS_PSK or OPc, although profile 15.03 defines them. SCP81 stays blocked without that PSK [DOC]. These values must reach Nuevatel by another route or not at all [INFERENCE] (OQ-26).
- No output files from other lots are in the folder [DOC] (OQ-1).
- ICCID has 20 characters in `.OUT` and 18 digits in `.sec.xml`, a point of care for the parser [DOC].
- `.card.xml` holds 10,000 IMSIs and serials and is not covered by `.gitignore` [DOC] (R15).

## P. Satpush v2.0 (`Satpush v2.0 Release Specification`, 2023-02-03)

**Facts [DOC].**

- Package `com.lsc.sat`; applet version 02.00; instance AID A0000001949147F23002000250534800.
- Requires Java Card 2.2.1, GlobalPlatform 2.2.1, UICC API Release 6 and USIM API Release 6; 17,710 bytes of EEPROM.
- Events: Profile Download, Formatted SMS-PP. Commands: Display Text, Get Input, Select Item, Launch Browser, Send USSD, Refresh, Send SMS.
- It has an Originating address installation parameter.
- Requires SST 26/27/29 and UST 28, the same services active on 15.05.

**Limits [DOC].** Only the specification is available, with no CAP or license. TAR and MSL are blank. It has 0 menu entries and no Setup Call. It does not appear in profiles 15.03 or 15.05, and the document does not name its owner.

**Inferences [INFERENCE].**

- The TAR derived from the AID is PSH, which conflicts with Service Engine PUSH on 15.03.
- Installing it requires RAM with KIC/KID.
- Its GlobalPlatform 2.2.1 requirement exceeds the GP 2.2 listed by 15.03, so compatibility is unproven.
- The shared service table suggests a relation with 15.05, which is unconfirmed (OQ-31).

## Q. Discovery and identity feed

**Discovery policy (PROPOSED).** Dawn Discovery runs only for new or unclassified SIMs, using the feed to avoid repeats. If the feed is missing, it does not send [INFERENCE: otherwise the repeat protection fails].

**Conflict to resolve.** In November 2023 IT, in a message from LLAVE, planned to remove Aircast's daily dawn Discovery because of its SMS volume, replacing it with a daily last-activity CSV [DOC]. On 2026-10-30 LLAVE asks to consider parameter-update SMS at dawn [LLAVE]. This proposal keeps dawn Discovery but narrows it. The regulatory side stays open (OQ-13).

**Feed evidence.**

- The CRM is the source; Ciro Caceres sends Mobiera a daily report of new SIMs, number, SIM, IMSI and last activity [LLAVE]. The platform takes a direct CRM extract; the report does not count as a source until validated (PROPOSED, ADR-6).
- A DWH process lists recently activated SIMs: SIM, IMSI, number, plan, age, last network activity [LLAVE]. Whether it is the same feed is OQ-29.
- August 2022: the second field of the feed carried the IMSI instead of the SIM number [DOC].
- October 2025: Mobiera reported that the subscriber file had not been delivered for some time, hurting SAT PUSH effectiveness [DOC].
- February–March 2026, ticket SPNT-133665: a "Solicitud ICCID" request was answered with IMSI data, and Mobiera's actual need was IMSI ranges [DOC].

**Inventory evidence.** The July 2022 notes already expected Aircast to help build a database of SIMs against electrical profile and SAT PUSH applet [DOC], which supports the Phase 0 count per profile and applet.

## R. Open questions (full register)

Moved from the brief on 2026-10-30. Answered or partly answered items keep their number and state what remains open.

1. **Coverage**: what share of active SIMs has a valid, current output file, per lot? Only NTE04570 is in the folder [DOC]; measuring needs a full snapshot of the base (OQ-29).
2. **Key validity**: were keys rotated after delivery, making the original output files obsolete? NTE04570 validity is untested [DOC].
3. **Sleepy**: what are its specification, proprietary security (key, command format) and licensing terms? *Partly answered*: installed on all SIMs [LLAVE], which documents contradict (OQ-27); AES or 3DES [DOC].
4. **Counters**: what validation mode does the profile use (greater-than vs exactly-plus-one)? Can Aircast export counters and key copies per ICCID? What is the reset policy? *Partly answered*: 15.05 file rules state "counter higher" [DOC]; 15.03 is unconfirmed.
5. **Master key**: does the manufacturer derive keys from a master key, and who holds it? *Still open*: "vasit, pero parcialmente" [LLAVE] does not say whether this means output files or a master key (OQ-26).
6. **S@T Browser**: what do MSL parameter 01 / data 02 mean on profile 15.03? *TAR answered on paper*: 534054 and 505348 [DOC]. Service Engine and PUSH declare no MSL [DOC].
7. **Mobiera contract**: what is its current status, given that the prior contract expired in July 2022? What rights does Nuevatel have to Aircast, the counters and the key copy? Mobiera was still requesting IMSI ranges in March 2026 [DOC], a sign of an active relationship [INFERENCE].
8. **SMSC**: what is its capacity (TPS)? What is the rule for external traffic? Can the SMS firewall filter OTA traffic by TAR as well as by PID and origin? *Partly answered*: the SAT PUSH application connects directly to the SMSC over SMPP, without the firewall [LLAVE].
9. **Team**: build, hire or partner for Java Card, OTA cryptography and HSM operations?
10. **Plaintext remediation**: who owns it, and by when? It now includes `NTE04570.card.xml` (R15).
11. **Stakeholders**: who are the business owner, the platform operators and the key custodians? Who approves the gates?
12. **Business case**: what do the Sleepy revenue share and Aircast cost, and what is the budget? None of these were provided.
13. **ATT**: what are the specific regulatory requirements for mass SIM messaging and subscriber data? *Still open.* Operational requirement recorded: consider the parameter-update SMS sent at dawn (Discovery) [LLAVE].
14. **Timeline**: are there target dates or deadlines? None were provided.
15. **Manufacturer request**: has the request for the new lot been sent, and when is a response expected? Is Valid the manufacturer of that lot, and has production started?
16. **HSM**: is an HSM available, and does it support 3DES? What are the procurement lead time and budget? On-premises or managed?
17. **Device mix**: what data exists on the handsets active on the network, to build the test matrix from?
18. **Coverage threshold**: what share of the reachable base justifies building the in-house engine, rather than keeping Aircast for existing lots and owning only new ones? *Still open.* A DWH process lists recently activated SIMs: SIM, IMSI, number, plan, age, last network activity [LLAVE].
19. **Aircast consumers**: which systems call the Aircast API directly today? *Answered*: a web page for mass campaigns by CSV, and VAS applications for purchases, reconnections and top-ups [LLAVE]. The inventory is OQ-30.
20. **OTA algorithms**: which KIC/KID algorithms and modes does each profile use for RAM and RFM, and does the HSM support them? KIC/KID/KIK on 15.03 have Algo ID 0x80 and 16 bytes, and `algoNumber=3` in `.sec.xml`; neither is decoded [DOC].
21. **Identity source**: which system is authoritative for the ICCID-to-IMSI mapping? *Answered*: the CRM; Ciro Caceres sends Mobiera a daily report of new SIMs, number, SIM, IMSI and last activity [LLAVE]. Not yet validated (OQ-29).
22. **Key rotation**: which key-rotation command do the cards accept?
23. **S@T push specification**: can Nuevatel obtain S@T 01.20, 01.21, 01.22 and 01.23? *Resolved*: they are in the folder, with 01.10 and 01.50 [DOC]. 3GPP TS 23.048 and ETSI TS 102 225/226 are still missing.
24. **Counter recovery**: how is a card's counter resynchronized after an uncertain send, especially if the profile requires exactly-plus-one?
25. **Plaintext exposure**: who could access the plaintext output files, since when, and do copies exist in version history, backups or synced devices? Who ran the analysis behind the NTE04570 aggregates, and on which machine?
26. **vas.it**: which lots' output files does vas.it hold, or does it hold a master key? `vas.it@nuevatel.com` is an internal Nuevatel mailing list [DOC]; that LLAVE's "vasit" means this list is [INFERENCE]. Links to OQ-5, OQ-10 and OQ-25.
27. **Sleepy reach** (to LLAVE): does "all" include NTE04570 and the G+D and Idemia lots? Was it installed by OTA or at the factory? Documents describe installation on SIMs with a defective engine and a base with several push engines [DOC].
28. **Firewall and Aircast path**: does the firewall block external PID 0x7F today, including on-net traffic? Does the direct connection in OQ-8 also apply to Aircast? IS-SU-TS 23915 §2.1.3 describes an Aircast SMPP client connecting to the SMSC and never mentions the firewall [DOC].
29. **Feed**: are the DWH process and Ciro Caceres's report the same? Was the October 2025 delivery failure fixed? Is there a full snapshot of the base? Can the CRM provide a direct extract, and what would validate the daily report as a source?
30. **VAS inventory**: which VAS applications call Aircast, and who owns each?
31. **Satpush v2.0**: who holds it, where are the CAP and license, and how does it relate to 15.05? It requires GlobalPlatform 2.2.1 while 15.03 lists GP 2.2 [DOC], and its derived TAR collides with PUSH on 15.03 [INFERENCE].
32. **eSIM**: does it stay out of scope, given that Sleepy would be on Nuevatel's eSIM?
33. **Rollback after a counter jump**: can Aircast send to a card again once the engine has jumped its counter? [INFERENCE: Aircast's counter would be lower and its packets rejected.] Until the lab proves a rollback, a jump is a one-way cutover per family.
34. **Aircast's own senders**: how are migrated SIMs excluded from Discovery and from campaigns already loaded in Aircast, which do not pass through the unified API? [INFERENCE]
