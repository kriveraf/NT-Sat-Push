---
title: "Addendum: Nuevatel SAT Platform brief"
status: final
created: 2026-10-22
updated: 2026-10-28
---

# Addendum: Nuevatel SAT Platform

Supporting detail for downstream PRD and architecture work. It contains **no key material**: keys are referred to only by type and custody.

## A. SIM profile 15.03 (technical summary)

- Java Card 3.0.1; USIM / ISIM / CSIM; BIP; Admin Agent and DNS Resolver (SCP81 support).
- Applets include S@T Browser (SBT), SmartRoaming, IMEI tracking, SIMChronize, AppBooster and others. The full list is to be confirmed with the manufacturer.
- **AppBooster is not Sleepy.** Sleepy is a separate Mobiera applet installed after issuance (section K).
- The USIM/GSM file tree was reviewed. The network keys it holds (e.g. Kc) are unrelated to OTA keys and out of scope.

### OTA applications

| Application | TAR | MSL (parameter / data) |
|---|---|---|
| RAM | 000000 | 01 / 02 |
| USIM_RFM | B00001 | 01 / 02 |
| SIM_RFM | B00010 | 01 / 02 |
| S@T Browser | **Not confirmed (OQ-6)** | Unknown |
| Sleepy (installed post-issuance) | 534C59 ("SLY") | 0 (see K) |

Correction recorded 2026-10-28: TAR B00010 is SIM_RFM, not the S@T Browser. The exact meaning of MSL parameter 01 / data 02 on this profile is still unconfirmed and must be checked against the manufacturer's specification before the engine design is settled (OQ-6).

### Keysets (by type and custody only)

| Keyset | Contents (type) | Owner / platform relevance |
|---|---|---|
| 01 | OTA keys KIC, KID, KIK; ADM1 | KIC/KID/KIK in scope (SCP80 OTA, key service). ADM1 goes to the support vault, not the platform |
| 03 | ADM3, KIK, ISD_TLS_PSK | In scope for SCP81 (PSK-TLS). ADM3 goes to the support vault |
| 10 | Network authentication (Ki, OPc) | **Out of scope**: stays in the HSS |

Custody status:

- OTA keys are unique per card and are delivered by the manufacturer as output files per lot. They cannot be reused across cards or lots. Many lots exist, past and current.
- Aircast keeps a copy of the keys in its database.
- Whether the keys are derived from a master key is unknown (OQ-5). If they are, whoever holds that master key is the strategic dependency.
- The contract-level and technical details of custody are partly unknown (OQ-7).
- The existing output files are stored in plaintext in a cloud-synced folder. They must be remediated first (OQ-10).

## B. Aircast capabilities that must be replaced or reproduced

- Northbound REST API: UstkRequest of type Text, Menu, Url, Call or Ussd. The Nuevatel unified send API stays compatible with it (I, ADR-1).
- SMSC connection over SMPP.
- Discovery: identifies each SIM's browser type through MO shortcodes, using a daily subscriber file as input (see F).
- OTA bytecode generation for RAM, RFM, S@T, Sleepy, WIB and Pico.
- Per-card storage of keys and anti-replay counters.

## C. Migration approach

1. Nuevatel orchestration calls a unified send API compatible with UstkRequest.
2. At first the Aircast driver serves every send.
3. The Nuevatel OTA engine is built in parallel and validated in the lab, per SIM family.
4. SIM families move to the Nuevatel driver one at a time, with rollback. A per-ICCID flag ensures that only one platform operates a SIM at a time.

Preconditions: contracted access to the Aircast API for the transition (OQ-7); counter export per ICCID (OQ-4); key coverage for the target families (OQ-1, OQ-2).

## D. Phase detail

| Phase | Key activities | Exit / blocker |
|---|---|---|
| 0. Diagnosis | Remediate plaintext output files (including version history, recycle bin, backups, synced devices) and establish who had access (OQ-25); per-lot coverage audit (metadata only, without opening secret files); key-validity check; Aircast counter-export test on sample ICCIDs; Mobiera contract review; SMSC TPS and firewall review; skills assessment; follow up the manufacturer request; start HSM procurement | Gate: feasibility conditions 2–4 (documentation, Sleepy decision, coverage) plus counter export, skills decision, owner, business case, and the Phase 5/6 fallback |
| 1. Inventory and orchestration | Campaigns, ICCID-keyed inventory, Discovery (including S@T environment variables, L), content | — |
| 2. Unified send API + Aircast driver | UstkRequest-compatible API; Aircast driver; callbacks and reporting | Pivot checkpoint: OQ-23 and counter export re-checked; fallback applied if open |
| 3. Key service | HSM (model chosen after OQ-16/OQ-20), custody, counters, import, rotation design, governance (N) | Starts after the Phase 0 gate |
| 4. Lab and minimal OTA engine | Card readers, test SIMs per family, handset matrix (including iPhone); SCP80 engine able to perform an RFM read; counter validation mode confirmed per family | Starts after the Phase 0 gate. Feasibility condition 1: real RFM read with positive proof of receipt, per SIM family. Rotate lots with confirmed plaintext exposure after this phase |
| 5. S@T push and menu | S@T push; menu cleanup and new menus | **Blocked** until the S@T Browser TAR/MSL (OQ-6) and the S@T push specification (OQ-23) are available |
| 6. Migration by SIM family | Counter import, per-ICCID ownership switch, per-family cutover with rollback; Aircast decommission criteria | **Blocked** until Aircast counters can be exported (OQ-4) |
| 7. Full independence | Nuevatel applet loaded via RAM or SCP81 (replacing Sleepy); rotation to Nuevatel-controlled keys | Gated by a lab spike on new-lot samples (R8) |

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

The answers feed OQ-1, OQ-2, OQ-4, OQ-5, OQ-6, OQ-20 and OQ-22 directly. Whether it has been sent is OQ-15.

## F. Test-matrix inputs

The known defects listed in the brief each need a lab test case: per SIM family for the Idemia S@T auto-accept issue, per handset for iPhone S@T, menu-entry checks for the dead entries, and ICCID-keyed reconciliation tests for the Discovery feed (IMSI vs ICCID mismatches). Every family also needs the condition-1 test: a real RFM read with a positive proof of receipt.

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
| P5 | Per-ICCID flag does not bind Aircast | Aircast SMPP bypasses the Nuevatel gateway | Aircast SMPP routed through the Nuevatel exit gate (ADR-5) |
| P6 | Firewall cannot filter what R11 needs | Firewall cannot inspect the TAR; two authorized origins in coexistence | OQ-8 expanded; Sleepy exposure sized via OQ-3 |
| P7 | Spending ahead of the gate | Phase 3 spend before the Phase 0 gate | Phases 1–2 start now; Phases 3–4 wait for the gate |

### Risk register (current roadmap, 2026-10-28)

Full table; the brief keeps only the five risks that gate the program.

| # | How it fails | Early warning | Mitigation now |
|---|---|---|---|
| R1 | **Unreachable base.** Most active SIMs lack valid output files, so the engine reaches only new lots and Aircast can never be retired (OQ-1, OQ-2, OQ-5). | Phase 0 coverage below threshold | Coverage is a Phase 0 gate criterion. Plan per family: in-house, stay on Aircast, or retire through SIM replacement. G4 and G7 measured on the reachable segment. |
| R2 | **Counters and keys locked in Aircast.** Mobiera does not cooperate, so the first in-house sends are rejected as replays (OQ-4, OQ-7). | No export on sample ICCIDs by the Phase 0 gate | Secure access and export rights at the Phase 0 gate. Test export on sample ICCIDs. Confirm the counter validation mode (OQ-4). |
| R3 | **Send API shaped by Aircast.** The UstkRequest-compatible contract cannot express what the Nuevatel engine needs (RAM/RFM, S@T push, SCP81). | An engine feature requires a contract change | Accepted trade-off. Keep orchestration independent of the driver; extend the contract in a versioned way. |
| R4 | **Skills and long-lead items.** OTA cryptography and HSM knowledge sit with one person; HSM procurement stalls Phase 3 (OQ-9, OQ-16). | No build, hire or partner decision at the Phase 0 gate | Decision is a gate criterion. Start HSM procurement in Phase 0. Two people per critical skill. |
| R5 | **Field incident.** A wrong mass send or a bad RFM write harms subscribers, draws ATT attention, and leadership halts the program (OQ-13). | Mass sends without canary or dual control | Per-campaign volume limits, canary then ramp, dual control, emergency stop, pre-tested rollback; consult ATT before the first mass campaign. |
| R6 | **Fragmentation.** It works in the lab but fails on real handsets and SIM families (iPhone, Idemia auto-accept) (OQ-17). | Results differ by family or handset | Lab validation per SIM family; handset matrix from the real device mix. |
| R7 | **No visible value.** Long plumbing, no change for subscribers, and the budget is cut (OQ-11, OQ-12). | No business owner or business case at the Phase 0 gate | Owner and business case are gate criteria; an early visible win via the Aircast driver; G8. |
| R8 | **Applet infeasible on old lots.** Loading a Nuevatel applet needs privileges only the manufacturer holds, so Sleepy stays (OQ-3, OQ-5). | Lab spike fails on samples | Treat Phase 7 as an option, gated by a lab spike on new-lot samples. |
| R9 | **Zombie migration.** Aircast and the new platform run side by side indefinitely, at double cost. | No decommission date after the pilot | Define decommission criteria before Phase 6 starts. |
| R10 | **Counter divergence.** Both platforms send to the same cards, so the cards reject packets as replays. | Any card receiving OTA from both | Per-ICCID ownership flag; single sender per card; counter export at cutover. |
| R11 | **Sleepy reachable by third parties.** At MSL 0, anyone able to send SMS-PP to TAR "SLY" reaches the applet. | OTA-class SMS from unauthorized origins seen at the firewall | SMS firewall admits PID 0x7F only from the authorized OTA origin (OQ-8). |
| R12 | **S@T push stalls.** The companion S@T specifications cannot be obtained, so Phase 5 never starts. | Specifications not in hand when Phase 4 ends | Request them early (OQ-23); keep menu changes on the Aircast driver meanwhile. |
| R13 | **Blocked at the finish line.** Phases 1–4 deliver but Phases 5 and 6 wait on external parties, leaving Nuevatel more dependent on Aircast. | OQ-23 or counter export still open at the end of Phase 2 | Fallback decided at the Phase 0 gate; pivot checkpoint after Phase 2. |

## I. Architecture decision records (proposed)

Inputs to `bmad-architecture`, not final decisions.

| ADR | Options considered | Trade-offs | Proposed |
|---|---|---|---|
| 1. Send API (revised 2026-10-28) | (a) UstkRequest-compatible unified send API with two drivers. (b) Nuevatel domain API with an Aircast adapter. (c) Events only. | (a) keeps existing consumers unchanged and makes the driver swap invisible, but ties the contract to Aircast's request shape (R3). (b) was the 2026-10-22 proposal. (c) does not fit synchronous menu pushes. | **(a)**, per the functional architecture. Extend the contract in a versioned way when the engine needs more than UstkRequest expresses. |
| 2. Crypto boundary | (a) Keys encrypted in the application database. (b) HSM releases keys at runtime. (c) Operations run inside the HSM; per-card keys stored only wrapped under the HSM master key. | (a) and (b) expose keys in application memory. (c) needs HSM support for the profiles' algorithms, possibly 3DES (OQ-16, OQ-20). | **(c)**. Separate keys per environment; the engine never sees master keys. |
| 3. Counter ownership in coexistence | (a) Both systems send to any card. (b) Single sender per card, switched by a per-ICCID flag, with Aircast's counters exported at cutover. | (a) makes counters diverge and cards reject packets (R10). (b) needs the flag and the export. | **(b)**. A hard rule for Phases 4–6. |
| 4. OTA engine sourcing | (a) Build in-house. (b) Buy another vendor's engine. (c) Partner for the crypto core; build the rest. | (b) swaps one dependency for another. (c) reduces skills risk (R4) if keys stay in Nuevatel's HSM. | **(a)**; (c) as fallback at the Phase 0 skills gate; (b) rejected. |
| 5. SMSC integration | (a) Shared SMPP binds. (b) Dedicated OTA bind behind a single exit gate, with its own throughput budget and SMS-firewall rules. | (a) cannot enforce OTA throttling or origin filtering. (b) makes volume limits, the emergency stop and the R11 firewall rule enforceable. | **(b)**. Aircast's SMPP traffic also passes through this exit gate, so the per-ICCID flag is enforced at the edge. Throughput budget depends on OQ-8. |
| 6. Inventory identity | (a) IMSI-keyed, fed by the daily file. (b) ICCID-keyed, with the IMSI mapping from the authoritative source. | (a) keeps today's Discovery mismatches. (b) addresses the root cause; S@T environment variables can supply ICCID directly (L). | **(b)**. Authoritative source to confirm (OQ-21). |

## J. Contract context

The prior Mobiera contract expired in July 2022 (OQ-7). The July 2022 email ("no dependency; Nuevatel keeps keys and control") conflicts with the Sleepy key and specification being held only by Mobiera, and with the anti-replay counters being held in Aircast (Mobiera software, hosted in Nuevatel's datacenter). Legal review is needed.

## K. Sleepy applet (Mobiera guide v9, January 2023)

- Package AID prefix 4D4F42434F ("MOBCO"); TAR 534C59 ("SLY").
- Requires Java Card 2.2.1 and the ETSI UICC/USIM APIs.
- About 8.6 KB of code and up to about 6.7 KB of NVRAM.
- Installed after issuance, with minimum security level 0, because it applies its own proprietary security. That security (key, algorithm, command format) is **not documented** in the guide.
- Its validation message uses PID 0x7F, DCS 0xF6 and ESM class 0x40.

**Implications.**

- The OTA keys (KIC/KID/KIK) are not enough to operate Sleepy. Its specification and key remain a Mobiera dependency (OQ-3).
- With MSL 0, any party able to send SMS-PP to TAR "SLY" reaches the applet. The SMS firewall must admit only the authorized OTA origin (R11).
- Feasibility condition 3: obtain the specification and key, or replace Sleepy with a Nuevatel applet (Phase 7).

## L. S@T specification (TCA S@T 01.00 v4.0.0, bytecode)

- Defines decks, cards and commands; a secure message (3DES, 8-byte MAC, SPI 0x02 / 0x04 / 0x06); and environment variables: ICCID, browser supplier, browser version, profile and buffer size.
- **Opportunity**: a deck can read the environment variables, so Nuevatel can build its own SIM inventory without Mobiera's Discovery.
- **Gap**: SAT Push needs companion documents that are not available: S@T 01.20 (session protocol), 01.21 (administration), 01.22 (pull) and 01.23 (push). It also needs 3GPP TS 23.048 and ETSI TS 102 225 / 102 226 (OQ-23).

## M. Functional architecture (proposed)

**Sources**

- OCS/BSS: balance and top-up events.
- CRM: audiences.
- HLR/HSS: IMSI/IMEI changes, SIM swap.
- Operator UI.

**Nuevatel platform**

- Orchestration: campaigns, inventory, Discovery, content.
- Unified send API, compatible with Aircast's UstkRequest.
- Two drivers behind it:
  - Aircast driver (transitional).
  - Nuevatel OTA engine: SCP80 with RAM/RFM and S@T first; SCP81 later.
- Key service, used only by the OTA engine.

**Outbound path**

SMPP gateway with SMS firewall (PID 0x7F, authorized origin only) → SMSC → network → handset → SIM applets addressed by TAR:

| Applet | TAR |
|---|---|
| RAM | 000000 |
| USIM_RFM | B00001 |
| SIM_RFM | B00010 |
| S@T Browser | Not confirmed (OQ-6) |
| Sleepy | 534C59 ("SLY") |
| Admin Agent (SCP81) | Not documented in the findings |

**Return path**

Proofs of receipt and MO messages → SMSC → engine → callbacks and KPIs.

**Design rules**

- A single exit gate to the network.
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
- The profile's validation mode (greater-than vs exactly-plus-one) is unconfirmed and drives the design (OQ-4).
- Migration from Aircast needs a per-ICCID flag, so only one platform operates a SIM at a time, plus an export of Aircast's counters.
- Confirm the validation mode per SIM family in the lab before any pilot. Under exactly-plus-one, a lost message leaves the card "uncertain"; a resynchronization procedure is needed before production (OQ-24).

**Rotation** (uses the KIK; the command the cards accept is OQ-22)

1. Generate new keys and store them as pending.
2. Test in the lab.
3. Send a real validation message.
4. Activate in waves, with a stop condition.
5. Retire the old version only after stability.

**Import of output files**

- A parser per SIM family.
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
