---
title: "Product Brief: Nuevatel SAT Platform"
status: final
created: 2026-10-22
updated: 2026-10-30
---

# Product Brief: Nuevatel SAT Platform

> Security note: this brief and its addendum contain no key material. Keys are referred to only by type and custody. Findings about lot NTE04570 are aggregates (counts, uniqueness, equality) supplied by the owner. No values are quoted, and the key files were not opened for this update.
>
> Source tags on facts added 2026-10-30: **[DOC]** document; **[LLAVE]** LLAVE's answer of 2026-10-30; **[INFERENCE]** untested inference. **Nothing has been validated on a real SIM yet.** Architecture changes from this update are marked PROPOSED.

## Executive Summary

Nuevatel (VIVA) owns its SIMs and subscribers. To manage them remotely it depends on Mobiera (the Aircast platform and the Sleepy applet) and on SIM manufacturers for the software, the applet and key custody.

The **Nuevatel SAT Platform** is an in-house SIM Application Toolkit and OTA management platform. It brings back in-house four layers that today sit with others:

- **Orchestration**: campaigns, inventory, Discovery, content and reporting.
- **OTA engine**: SCP80 over SMS first (RAM/RFM and S@T), SCP81 over HTTPS/PSK-TLS later.
- **Key service**: HSM-backed custody, per-card counters, rotation to Nuevatel-controlled keys.
- **Applet** (eventually): a Nuevatel Java Card applet that replaces Sleepy.

Orchestration calls a single **unified send API**, compatible with Aircast's UstkRequest, behind which sit two drivers: Aircast (transitional) and the Nuevatel OTA engine. SIMs move from one driver to the other per SIM family. Consumers keep the request shape and change only their endpoint (PROPOSED, ADR-3).

**Feasibility verdict: still viable, and improved. The same four conditions apply.**

1. **Lab validation per SIM family: open.** No real RFM read or positive proof of receipt exists yet.
2. **Complete manufacturer documentation: partial.** S@T TARs, the Admin Agent TAR and the S@T specifications are in hand [DOC]. Still missing: the meaning of MSL 01/02, the algorithm decoding, the counter mode on 15.03, the PSK, and confirmation from Valid.
3. **Sleepy decision: improved.** S@T can avoid Sleepy on SIMs where it works [INFERENCE]. The decision is still required: Sleepy was proposed for SIMs with a defective push engine [DOC], so the gain has to be measured per family.
4. **Key coverage of the active base: unchanged, and the largest risk.** Only lot NTE04570 (10,000 SIMs) has output files in hand [DOC], their validity is untested, and the base has not been measured.

A formal request to the SIM manufacturer has been prepared for the lot ordered on 2026-10-22. That lot is the natural place to set up Nuevatel-controlled custody from day one, and the request now also covers the findings of this update (addendum E). The existing output files are stored in plaintext in a cloud-synced folder and must be remediated first.

## Decisions Requested (PROPOSAL)

1. Approve Phase 0 (diagnosis) and the remediation of plaintext output files as the first action.
2. Adopt the unified send API with two drivers (Aircast, then the Nuevatel engine) as the migration approach.
3. Name a business owner and the gate approvers (OQ-11).
4. At the Phase 0 gate, secure contractual access to Aircast for the transition and the right to export counters and key copies per ICCID (R2). Phase 6 depends on this (see Blockers and sequencing).
5. Start long-lead work in Phase 0: HSM procurement and the build, hire or partner decision (R4). Select the HSM model only after the algorithms and 3DES needs are known (OQ-16, OQ-20).
6. Decide on Sleepy: obtain the specification, key and licensing terms from Mobiera, or plan its replacement by a Nuevatel applet (OQ-3).
7. Send the expanded manufacturer request before the 2026-10-22 lot enters production (OQ-15).
8. Authorize the two new Phase 0 probes: a scoped SMPP sniffer on test lines, and a lab test with an NTE04570 SIM.
9. Plan the move of the web campaign page and the VAS applications to the unified send API before Phase 6 (ADR-3, OQ-30).

## Problem and Opportunity

**Problem.** Nuevatel depends on vendors for SIM remote management:

- **Aircast (Mobiera)** runs in Nuevatel's datacenter. It drives campaigns and Discovery, generates OTA bytecode, and holds a copy of the OTA keys and the per-card anti-replay counters. Keys sit in an AES-encrypted database, out of reach of its operators [DOC]. Its capability inventory is in addendum B.
- **Sleepy (Mobiera)** is a proprietary applet (TAR "SLY", distinct from AppBooster) installed after issuance. It has its own AES or 3DES encryption, independent of the OTA keys [DOC]; its key and command format remain undocumented. OTA keys alone cannot operate it; its specification and key stay with Mobiera, paid through revenue share (addendum K). It is reported on all SIMs [LLAVE], while project documents describe it for defective SIMs [DOC] (OQ-27).
- **The SIM estate is mixed**: several manufacturers (Idemia, G+D and Valid) across many lots. The Valid link rests only on the NTE04570 lot header and the profile name 15.03_VA, and is to be confirmed with Valid [DOC].
- **Known defects**:
  - S@T auto-accept behavior on some Idemia SIMs.
  - S@T problems on iPhone.
  - An obsolete SIM menu with many dead entries.
  - A fragile Discovery feed: daily subscriber file, IMSI vs ICCID mismatches, and a delivery failure reported in October 2025 [DOC].

**Cost of the status quo.**

- Nuevatel cannot change the SIM menu, fix defective lots, or launch SIM-based services without a vendor in the loop.
- Sleepy revenue goes to the vendor, and subscribers see a degraded SIM menu.
- Unclear key custody and plaintext output files are a security and regulatory exposure.

**Opportunity.**

- Profile 15.03 already supports Java Card 3.0.1, BIP and SCP81, and OTA keys are unique per card (unique across all 10,000 cards of NTE04570 [DOC]).
- The S@T specification (S@T 01.00) defines environment variables (ICCID, browser supplier, version, profile, buffer size) that a deck can read. This makes a self-built SIM inventory possible without Mobiera's Discovery (addendum L).
- The S@T companion specifications are now in hand [DOC], which removes the paper blocker on Phase 5.
- The new lot gives custody a clean start.
- Owning the platform makes the SIM a channel Nuevatel controls, integrated with BSS/OCS events such as balance and top-ups.

## Target Users and Stakeholders

The groups below are inferred from the scope and are **to be confirmed** (OQ-11):

- **Platform operators**: whoever runs campaigns, menus and content (e.g. marketing / VAS). Aircast campaigns are used by Marketing [DOC].
- **Engineering and operations**: OSS/IT, core network (SMSC, HLR/HSS, SMS firewall), and the BSS/OCS and CRM owners.
- **Aircast consumers**: the web page for mass campaigns by CSV, and VAS applications for purchases, reconnections and top-ups [LLAVE].
- **Security and key custodians**: HSM operation and dual-control officers.
- **Legal, regulatory and procurement**: ATT alignment, the Mobiera and SIM-manufacturer contracts.
- **Subscribers**: indirect users of the SIM menu and pushed content.

## Vision

Nuevatel owns the whole SIM remote-management chain (orchestration, OTA engine, key custody and applet), integrated with its own network and BSS. Vendors become replaceable suppliers rather than gatekeepers.

## Goals and Success Criteria (PROPOSALS — to validate)

| # | Goal | Proposed measure | Target |
|---|------|------------------|--------|
| G1 | Know the estate | Share of active SIMs with a valid, current output file, per lot | Baseline in Phase 0; target TBD |
| G2a | Secure custody | Output files held in plaintext | 0 after remediation |
| G2b | Secure custody | Key and mass-send operations under dual control, with an audit trail | 100% |
| G3 | Own orchestration | New campaigns run through the Nuevatel orchestrator | 100% after Phase 2 |
| G4 | Own the OTA engine | SIMs per validated family reached by the Nuevatel SCP80 engine with a positive proof of receipt and no counter or replay failures | Rate TBD; rollback tested |
| G5a | Fix the experience | Dead SIM-menu entries on managed lots | 0 |
| G5b | Fix the experience | Discovery IMSI/ICCID mismatch rate | Baseline, then a reduction TBD |
| G6 | Remove the Sleepy dependency | SIMs that depend on Sleepy | Trend to 0; date TBD (OQ-3) |
| G7 | Exit Aircast | Production traffic on the Nuevatel engine; Aircast decommissioned | Date TBD after the pilot; per-family plan (R1) |
| G8 | Show value early | First subscriber-facing improvement in production (e.g. menu cleanup) | Within TBD months of start (R7) |

## Scope

**In scope:**

- Orchestration: campaigns, inventory, Discovery, content and menus.
- Unified send API with an Aircast driver and a Nuevatel OTA engine driver.
- OTA engine: SCP80 with RAM/RFM and S@T first, SCP81 later.
- Key service with HSM integration.
- Integrations: SMSC (SMPP), SMS firewall (external PID 0x7F block), OCS/BSS, CRM, HLR/HSS, operator UI.
- Observability, audit and security controls.
- Migration from Aircast by SIM family, with rollback.
- Test lab: card readers, test SIMs per family, handset matrix.

**Out of scope (for now):**

- Ki/OPc and network authentication (keyset 10 stays in the HSS). The platform never stores Ki, OPc, PIN, PUK or ADM.
- Network keys in the USIM/GSM file tree (e.g. Kc); they are unrelated to OTA keys.
- eSIM/SGP profiles. No eSIM documentation exists; the only mention is Mobiera's 2023 remark that Sleepy is on Nuevatel's eSIM [DOC] (OQ-32).
- Replacing the SIM manufacturer.
- Building a new OCS/BSS.

## Functional Architecture (PROPOSED)

Detail is in addendum M.

- **Sources**: OCS/BSS (balance and top-up events), CRM (audiences and identity), HLR/HSS (IMSI/IMEI changes, SIM swap), operator UI.
- **Nuevatel platform**: orchestration (campaigns, inventory, Discovery, content) → unified send API (UstkRequest-compatible) → Aircast driver (transitional) or Nuevatel OTA engine. Only the OTA engine uses the key service.
- **Outbound path (PROPOSED, revised 2026-10-30)**: dedicated SMPP bind directly to the SMSC (ADR-5) → network → handset → SIM applets addressed by TAR (RAM, USIM_RFM, SIM_RFM, S@T 534054, PSH 505348, Sleepy, Admin Agent B20100 for SCP81).
- **Return path**: proofs of receipt and MO messages via the SMSC → engine → callbacks and KPIs.
- **Design rules**: see Key Architecture Decisions 2, 3 and 5.

## Key Service (PROPOSED)

Detail is in addendum N.

- **Custody and HSM**: per-card KIC/KID/KIK wrapped under an HSM master key held in split custody across at least two HSMs (3DES support to verify, OQ-16). Ki/OPc go to the HSS; PIN, PUK and ADM go to a support vault.
- **Counters**: atomic per-card reservation in a strongly consistent store. The validation mode (greater-than vs exactly-plus-one) drives the design. Profile 15.05 states "counter higher" in its file rules [DOC]; 15.03 is unconfirmed (OQ-4).
- **Rotation, import and governance**: rotation via the KIK in waves with a stop condition; two-person import with no key values in reports; immutable audit log, per-campaign volume limits and an emergency stop. KID = KIK on NTE04570 weakens this rotation path (R14).

## Key Architecture Decisions (PROPOSED)

Detail is in addendum I. These are inputs to `bmad-architecture`.

1. **Send API**: a unified send API compatible with Aircast's UstkRequest, with two drivers. This replaces the earlier domain-API proposal; the coupling to Aircast's request shape is an accepted trade-off (R3). The Aircast consumers now known, a campaign web page and VAS applications [LLAVE], reinforce the case for compatibility.
2. **Crypto boundary**: OTA operations run inside the HSM; per-card keys are stored only wrapped; the engine never sees master keys.
3. **Single writer per card (PROPOSED, revised 2026-10-30)**: a per-ICCID flag ensures only one platform operates a SIM at a time, but it binds only unified-API traffic, not the network edge. The web page and VAS applications therefore move to the unified API before Phase 6 (OQ-30), and Aircast's own senders must exclude migrated SIMs (OQ-34). Counters are reserved transactionally before sending; Aircast's are exported or jumped at cutover (R2).
4. **Engine**: built in-house, as the vision states. Partnering for the crypto core is the fallback if the Phase 0 skills decision calls for it. Buying another vendor's engine is rejected.
5. **SMSC (PROPOSED, reverses the 2026-10-28 exit gate)**: own traffic goes directly to the SMSC over a dedicated SMPP bind, restricted by IP and system_id, with its own TPS limit and an emergency stop (the SAT PUSH application connects directly, without the firewall [LLAVE]). The SMS firewall's only role is to block external PID 0x7F (OQ-8, OQ-28). Aircast's traffic is not routed through Nuevatel.
6. **Inventory identity (PROPOSED, revised 2026-10-30)**: keyed on ICCID, with a direct CRM extract as the source of the IMSI mapping [LLAVE] and prior validation against lot NTE04570, which covers only its own 10,000 SIMs. The daily report does not count as a source until validated (OQ-29). S@T environment variables can feed the inventory directly.

## Constraints and Principles

- **No key material**: never store, copy or print key material in documents or the repository.
- **Security first**: HSM custody, dual control for key and mass-send operations, auditable logs, separate lab / pre-prod / prod keys.
- **Network edge (PROPOSED, revised 2026-10-30)**: own traffic uses a dedicated bind, and the SMS firewall only blocks external PID 0x7F (ADR-5). This matters most for Sleepy, which runs at MSL 0, and for S@T if its MSL is undefined (R11).
- **Regulatory**: alignment with ATT (Bolivia) on mass messaging and subscriber data.
- **Change safety**: phased delivery, lab validation per SIM family, and a tested rollback before any production change. A counter jump without a proven rollback to Aircast is the one exception, and needs explicit approval per family at cutover (OQ-33).

## Vendor and Document Dependencies

| Dependency | What we depend on | Exit path |
|---|---|---|
| Mobiera Aircast | API, Discovery, bytecode, key copy, **anti-replay counters** | Aircast driver during transition; counter route (R2); per-family cutover |
| Mobiera Sleepy | Specification, security and key; revenue share | Obtain spec and key, replace with a Nuevatel applet, or use S@T where it works |
| SIM manufacturers | Output files; possibly a master key; algorithms, MSL, counter policy, PSK | Request for the new lot (addendum E); rotation to Nuevatel keys |
| Specifications | S@T 01.10, 01.20, 01.21, 01.22, 01.23 and 01.50 in hand [DOC]; 3GPP TS 23.048 and ETSI TS 102 225/226 not in the folder [DOC] | Obtain the remaining standards before the Phase 0 lab test, which needs the 23.048 packet format [INFERENCE] |

## Phased Roadmap

Detail is in addendum D.

0. **Diagnosis**: remediate plaintext output files, including version history, recycle bin, backups and synced devices; measure key coverage of the active base; test Aircast counter export on sample ICCIDs; review the Mobiera contract; follow up the manufacturer request; SMSC capacity; team skills; business case; start HSM procurement. Also:
   - A scoped sniffer on Aircast's SMPP bind, limited to test lines, with authorization and later deletion. It shows the traffic but does not yield the Sleepy key.
   - A count of SIMs per profile and applet from Aircast.
   - A full snapshot of the base, to measure OQ-1.
   - A lab test with an NTE04570 SIM: an RFM read, and a push to TARs 505348 (PSH) and 534054, with and without security. This is a single-lot probe; it does not satisfy condition 1. It uses only the test SIMs' keys, under dual control and outside the repository.

   *Gate (proposed): coverage measured per lot (condition 4); manufacturer documentation received (condition 2); Sleepy decision taken (condition 3); counter route decided, either export proven and contracted or a jump test passed; build, hire or partner decided; business owner and business case approved; fallback decided for Phases 5 and 6 (if the lab does not prove push on a family, S@T stays on the Aircast driver there and the engine covers RAM/RFM only; without a proven counter route, the engine serves new lots only).*
1. **Inventory and orchestration**: campaigns, ICCID-keyed inventory, Discovery and content. Discovery at dawn is limited to new or unclassified SIMs, using the feed to avoid repeats (PROPOSED, addendum Q).
2. **Unified send API with the Aircast driver**: UstkRequest-compatible; campaigns run through Nuevatel. The web page and VAS applications start moving to it (PROPOSED).
3. **Key service**: HSM, custody, counters, import and governance.
4. **Lab and minimal OTA engine**: an RFM read with a positive proof of receipt, per SIM family (condition 1).
5. **S@T push and menu**.
6. **Migration by SIM family**, with rollback.
7. **Full independence**: a Nuevatel applet via RAM or SCP81, and rotation to Nuevatel-controlled keys. SCP81 stays blocked on NTE04570 without the PSK [DOC].

**Blockers and sequencing.** Phases 1–4 have no external blocker. Phases 1–2 keep their value even if the Phase 0 gate fails, so they can start now; Phases 3–4 wait for the gate. A pivot checkpoint at the end of Phase 2 re-checks the S@T lab result and the counter route, and applies the fallback if either is still open. If exposure of the plaintext output files is confirmed (OQ-25), affected lots are rotated after Phase 4 rather than in Phase 7.

Phase 5 is unblocked on paper: the TAR and the S@T specifications are in hand (OQ-6, OQ-23) [DOC]. The meaning of the MSL stays open, and the spec does not prove how each SIM family behaves. Phase 6 is blocked until Aircast counters can be exported or, in counter-higher families, a counter jump is proven in the lab (OQ-4, OQ-33), and until the web page and VAS applications have moved (OQ-30).

## Risks and Mitigations (pre-mortem)

Two pre-mortems (2026-10-22, failure by April 2028; 2026-10-28, stall by October 2028) are in addendum H with the full register (R1–R15). The five risks that gate the program:

- **R1 Unreachable base**: most active SIMs lack valid output files, so Aircast can never be retired (OQ-1, OQ-2, OQ-5). *Mitigation*: coverage is a Phase 0 gate criterion; plan per SIM family.
- **R2 Counters and keys locked in Aircast**: without an export or another counter route, the first in-house sends are rejected as replays (OQ-4, OQ-7). *Mitigation*: secure access and export rights at the Phase 0 gate; test export on sample ICCIDs. In counter-higher families, export may be unnecessary if the engine starts above anything Aircast used, with a single sender per SIM [INFERENCE, needs a lab test]. 15.03 is still unconfirmed. A jump is treated as a one-way cutover per family unless the lab proves a rollback to Aircast (OQ-33).
- **R10 Counter divergence**: both platforms send to the same cards. *Mitigation*: per-ICCID ownership flag and a single sender per card, which needs the consumer move (ADR-3).
- **R11 Unsecured push reachable by third parties**: at MSL 0, any SMS-PP to TAR "SLY" reaches Sleepy. S@T may share the exposure if its MSL is undefined, allowing a Simjacker-type push [INFERENCE, to be tested]. The risk is sized at the worst case, the whole base, until OQ-27 is answered. *Mitigation*: firewall block on external PID 0x7F (OQ-28); lab test of both S@T TARs in Phase 0; MSL with CC and counter on the new lot.
- **R13 Blocked at the finish line**: Phases 1–4 deliver but Phases 5 and 6 wait on lab proofs or parties who never deliver, leaving Nuevatel more dependent on Aircast. *Mitigation*: fallback decided at the Phase 0 gate; pivot checkpoint at the end of Phase 2.

**Standing risks:**

- **Plaintext exposure** (OQ-10): output files sit in plaintext in a cloud-synced folder; remediation is the first action of Phase 0.
- **R14 KID = KIK**: both keys are identical on all 10,000 NTE04570 cards [DOC], so whoever can use one holds the other and rotation via KIK gives less isolation [INFERENCE]. *Mitigation*: ask the manufacturer; require KID ≠ KIK on the new lot; confirm the card state in the lab.
- **R15 Identifiers outside .gitignore**: `NTE04570.card.xml` holds 10,000 IMSIs and serials [DOC]. `git check-ignore` shows that `.gitignore` does not cover it, and `docs/` is untracked, so a `git add docs/` would commit it. *Mitigation*: extend `.gitignore` and include the file in the Phase 0 remediation.
- **Contract tension**: Mobiera's July 2022 email states that there is no dependency and that Nuevatel keeps the keys and control. Yet the Sleepy key sits with Mobiera and the counters sit in Aircast. Legal review is needed before Phase 2 (Aircast driver).

## Open Questions

These questions gate the decisions requested. The full register, OQ-1 to OQ-34 with status and sources, is in addendum R; numbers are stable.

- **OQ-1 Coverage**: what share of active SIMs has a valid, current output file, per lot? Only NTE04570 is in the folder [DOC]; measuring needs a full snapshot of the base (OQ-29).
- **OQ-3 Sleepy**: what are its specification, proprietary security (key, command format) and licensing terms? *Partly answered*: installed on all SIMs [LLAVE], which documents contradict (OQ-27); AES or 3DES [DOC].
- **OQ-4 Counters**: what validation mode does the profile use (greater-than vs exactly-plus-one)? Can Aircast export counters and key copies per ICCID? What is the reset policy? *Partly answered*: 15.05 file rules state "counter higher" [DOC]; 15.03 is unconfirmed.
- **OQ-5 Master key**: does the manufacturer derive keys from a master key, and who holds it? *Still open*: "vasit, pero parcialmente" [LLAVE] does not say whether this means output files or a master key (OQ-26).
- **OQ-8 SMSC**: what is its capacity (TPS)? What is the rule for external traffic? Can the SMS firewall filter OTA traffic by TAR as well as by PID and origin? *Partly answered*: the SAT PUSH application connects directly to the SMSC over SMPP, without the firewall [LLAVE].
- **OQ-27 Sleepy reach** (to LLAVE): does "all" include NTE04570 and the G+D and Idemia lots? Was it installed by OTA or at the factory? Documents describe installation on SIMs with a defective engine and a base with several push engines [DOC].
- **OQ-28 Firewall and Aircast path**: does the firewall block external PID 0x7F today, including on-net traffic? Does the direct connection in OQ-8 also apply to Aircast? IS-SU-TS 23915 §2.1.3 describes an Aircast SMPP client connecting to the SMSC and never mentions the firewall [DOC].
- **OQ-33 Rollback after a counter jump**: can Aircast send to a card again once the engine has jumped its counter? [INFERENCE: Aircast's counter would be lower and its packets rejected.] Until the lab proves a rollback, a jump is a one-way cutover per family.
