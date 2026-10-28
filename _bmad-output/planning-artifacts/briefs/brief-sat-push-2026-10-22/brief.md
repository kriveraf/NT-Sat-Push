---
title: "Product Brief: Nuevatel SAT Platform"
status: final
created: 2026-10-22
updated: 2026-10-28
---

# Product Brief: Nuevatel SAT Platform

> Security note: this brief and its addendum contain no key material. Keys are referred to only by type and custody. Secret files are not read or quoted.

## Executive Summary

Nuevatel (VIVA) owns its SIMs and subscribers. To manage them remotely it depends on Mobiera (the Aircast platform and the Sleepy applet) and on SIM manufacturers for the software, the applet and key custody.

The **Nuevatel SAT Platform** is an in-house SIM Application Toolkit and OTA management platform. It brings back in-house four layers that today sit with others:

- **Orchestration**: campaigns, inventory, Discovery, content and reporting.
- **OTA engine**: SCP80 over SMS first (RAM/RFM and S@T), SCP81 over HTTPS/PSK-TLS later.
- **Key service**: HSM-backed custody, per-card counters, rotation to Nuevatel-controlled keys.
- **Applet** (eventually): a Nuevatel Java Card applet that replaces Sleepy.

Orchestration calls a single **unified send API**, compatible with Aircast's UstkRequest, behind which sit two drivers: Aircast (transitional) and the Nuevatel OTA engine. SIMs move from one driver to the other per SIM family, so consumers do not change.

**Feasibility verdict: viable, with four conditions.**

1. Lab validation per SIM family (manufacturer + profile + version), with a real RFM read and a positive proof of receipt.
2. Complete manufacturer documentation: algorithms, TAR, MSL and counter policy.
3. A decision on Sleepy: obtain its specification and key, or replace it with a Nuevatel applet.
4. Measured key coverage of the active SIM base.

A formal request to the SIM manufacturer has been prepared for the lot ordered on 2026-10-22. That lot is the natural place to set up Nuevatel-controlled custody from day one. The existing output files are stored in plaintext in a cloud-synced folder and must be remediated first.

## Decisions Requested (PROPOSAL)

1. Approve Phase 0 (diagnosis) and the remediation of plaintext output files as the first action.
2. Adopt the unified send API with two drivers (Aircast, then the Nuevatel engine) as the migration approach.
3. Name a business owner and the gate approvers (OQ-11).
4. At the Phase 0 gate, secure contractual access to Aircast for the transition and the right to export counters and key copies per ICCID (R2). Migration (Phase 6) is blocked without the counter export.
5. Start long-lead work in Phase 0: HSM procurement and the build, hire or partner decision (R4). Select the HSM model only after the algorithms and 3DES needs are known (OQ-16, OQ-20).
6. Decide on Sleepy: obtain the specification, key and licensing terms from Mobiera, or plan its replacement by a Nuevatel applet (OQ-3).

## Problem and Opportunity

**Problem.** Nuevatel depends on vendors for SIM remote management:

- **Aircast (Mobiera)** runs in Nuevatel's datacenter. It drives campaigns and Discovery, generates OTA bytecode, and holds a copy of the OTA keys and the per-card anti-replay counters. Its capability inventory is in addendum B.
- **Sleepy (Mobiera)** is a proprietary applet (TAR "SLY", distinct from AppBooster) installed after issuance, with its own undocumented security. OTA keys alone cannot operate it; its specification and key stay with Mobiera, paid through revenue share (addendum K).
- **The SIM estate is mixed**: several manufacturers (Idemia, G+D, a Thales/Gemalto-style profile) across many lots.
- **Known defects**:
  - S@T auto-accept behavior on some Idemia SIMs.
  - S@T problems on iPhone.
  - An obsolete SIM menu with many dead entries.
  - A fragile Discovery feed (daily subscriber file, IMSI vs ICCID mismatches).

**Cost of the status quo.**

- Nuevatel cannot change the SIM menu, fix defective lots, or launch SIM-based services without a vendor in the loop.
- Sleepy revenue goes to the vendor, and subscribers see a degraded SIM menu.
- Unclear key custody and plaintext output files are a security and regulatory exposure.

**Opportunity.**

- Profile 15.03 already supports Java Card 3.0.1, BIP and SCP81, and OTA keys are unique per card.
- The S@T specification (TCA S@T 01.00) defines environment variables (ICCID, browser supplier, version, profile, buffer size) that a deck can read. This makes a self-built SIM inventory possible without Mobiera's Discovery (addendum L).
- Legacy assets exist: an in-house Java SATClient library and Gemalto LinqUs Push Manager 5.1 documentation.
- The new lot gives custody a clean start.
- Owning the platform makes the SIM a channel Nuevatel controls, integrated with BSS/OCS events such as balance and top-ups.

## Target Users and Stakeholders

The groups below are inferred from the scope and are **to be confirmed** (OQ-11):

- **Platform operators**: whoever runs campaigns, menus and content (e.g. marketing / VAS).
- **Engineering and operations**: OSS/IT, core network (SMSC, HLR/HSS, SMS firewall), and the BSS/OCS and CRM owners.
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
- Integrations: SMSC (SMPP), SMS firewall, OCS/BSS, CRM, HLR/HSS, operator UI.
- Observability, audit and security controls.
- Migration from Aircast by SIM family, with rollback.
- Test lab: card readers, test SIMs per family, handset matrix.

**Out of scope (for now):**

- Ki/OPc and network authentication (keyset 10 stays in the HSS). The platform never stores Ki, OPc, PIN, PUK or ADM.
- Network keys in the USIM/GSM file tree (e.g. Kc); they are unrelated to OTA keys.
- eSIM/SGP profiles.
- Replacing the SIM manufacturer.
- Building a new OCS/BSS.

## Functional Architecture (PROPOSED)

Detail is in addendum M.

- **Sources**: OCS/BSS (balance and top-up events), CRM (audiences), HLR/HSS (IMSI/IMEI changes, SIM swap), operator UI.
- **Nuevatel platform**: orchestration (campaigns, inventory, Discovery, content) → unified send API (UstkRequest-compatible) → Aircast driver (transitional) or Nuevatel OTA engine. Only the OTA engine uses the key service.
- **Outbound path**: SMPP gateway with SMS firewall (PID 0x7F, authorized origin only) → SMSC → network → handset → SIM applets addressed by TAR (RAM, USIM_RFM, SIM_RFM, S@T Browser, Sleepy, Admin Agent for SCP81).
- **Return path**: proofs of receipt and MO messages via the SMSC → engine → callbacks and KPIs.
- **Design rules**: see Key Architecture Decisions 2, 3 and 5.

## Key Service (PROPOSED)

Detail is in addendum N.

- **Custody and HSM**: per-card KIC/KID/KIK wrapped under an HSM master key held in split custody across at least two HSMs (3DES support to verify, OQ-16). Ki/OPc go to the HSS; PIN, PUK and ADM go to a support vault.
- **Counters**: atomic per-card reservation in a strongly consistent store. The profile's validation mode (greater-than vs exactly-plus-one) is unconfirmed and drives the design (OQ-4).
- **Rotation, import and governance**: rotation via the KIK in waves with a stop condition; two-person import with no key values in reports; immutable audit log, per-campaign volume limits and an emergency stop.

## Key Architecture Decisions (PROPOSED)

Detail is in addendum I. These are inputs to `bmad-architecture`.

1. **Send API**: a unified send API compatible with Aircast's UstkRequest, with two drivers. This replaces the earlier domain-API proposal; the coupling to Aircast's request shape is an accepted trade-off (R3).
2. **Crypto boundary**: OTA operations run inside the HSM; per-card keys are stored only wrapped; the engine never sees master keys.
3. **Single writer per card**: a per-ICCID flag ensures only one platform (Aircast or Nuevatel) operates a SIM at a time; counters are reserved transactionally before sending, and Aircast's are exported at cutover.
4. **Engine**: built in-house, as the vision states. Partnering for the crypto core is the fallback if the Phase 0 skills decision calls for it. Buying another vendor's engine is rejected.
5. **SMSC**: a dedicated OTA SMPP bind behind a single exit gate, with its own throughput budget and SMS-firewall rules (OQ-8). Aircast's SMPP traffic also passes through this gate, so the per-ICCID ownership flag is enforced at the network edge.
6. **Inventory identity**: keyed on ICCID, with the IMSI mapping taken from the authoritative source rather than the daily file (OQ-21). S@T environment variables can feed it directly.

## Constraints and Principles

- **No key material**: never store, copy or print key material in documents or the repository.
- **Security first**: HSM custody, dual control for key and mass-send operations, auditable logs, separate lab / pre-prod / prod keys.
- **Network edge**: the SMS firewall admits OTA SMS-PP (PID 0x7F) only from the authorized origin. This matters most for Sleepy, which runs at MSL 0.
- **Regulatory**: alignment with ATT (Bolivia) on mass messaging and subscriber data.
- **Change safety**: phased delivery, lab validation per SIM family, and a tested rollback before any production change.

## Vendor and Document Dependencies

| Dependency | What we depend on | Exit path |
|---|---|---|
| Mobiera Aircast | API, Discovery, bytecode, key copy, **anti-replay counters** | Aircast driver during transition; export counters (and key copies) per ICCID; per-family cutover |
| Mobiera Sleepy | Specification, proprietary security and key (Mobiera only); revenue share | Obtain spec and key, or replace with a Nuevatel applet via RAM/SCP81 |
| SIM manufacturers | Per-lot output files; possibly a master key; algorithms, TAR/MSL, counter policy | Formal request for the new lot; custody terms; rotation to Nuevatel keys |
| Specifications | TCA S@T 01.20 (session), 01.21 (admin), 01.22 (pull), 01.23 (push); 3GPP TS 23.048; ETSI TS 102 225/226 | Obtain before Phase 5 (OQ-23) |

## Phased Roadmap

Detail is in addendum D.

0. **Diagnosis**: remediate plaintext output files, including version history, recycle bin, backups and synced devices; measure key coverage of the active base; test Aircast counter export on sample ICCIDs; review the Mobiera contract; follow up the manufacturer request; SMSC capacity; team skills; business case; start HSM procurement.
   *Gate (proposed): coverage measured per lot (condition 4); manufacturer documentation received (condition 2); Sleepy decision taken (condition 3); counter export proven and contracted; build, hire or partner decided; business owner and business case approved; fallback decided for Phases 5 and 6 (without the push specification, S@T stays on the Aircast driver and the engine covers RAM/RFM only; without counter export, the engine serves new lots only).*
1. **Inventory and orchestration**: campaigns, ICCID-keyed inventory, Discovery and content.
2. **Unified send API with the Aircast driver**: UstkRequest-compatible; campaigns run through Nuevatel.
3. **Key service**: HSM, custody, counters, import and governance.
4. **Lab and minimal OTA engine**: an RFM read with a positive proof of receipt, per SIM family (condition 1).
5. **S@T push and menu**.
6. **Migration by SIM family**, with rollback.
7. **Full independence**: a Nuevatel applet via RAM or SCP81, and rotation to Nuevatel-controlled keys.

**Blockers and sequencing.** Phases 1–4 have no external blocker. Phases 1–2 keep their value even if the Phase 0 gate fails, so they can start now; Phases 3–4 wait for the gate. A pivot checkpoint at the end of Phase 2 re-checks OQ-23 and the counter export and applies the fallback if either is still open. If exposure of the plaintext output files is confirmed (OQ-25), affected lots are rotated after Phase 4 rather than in Phase 7. Phase 5 is blocked until the S@T Browser TAR/MSL and the S@T push specification are available (OQ-6, OQ-23). Phase 6 is blocked until Aircast counters can be exported (OQ-4).

## Risks and Mitigations (pre-mortem)

Two pre-mortems (2026-10-22, failure by April 2028; 2026-10-28, stall by October 2028) are in addendum H with the full register (R1–R13). The five risks that gate the program:

- **R1 Unreachable base**: most active SIMs lack valid output files, so Aircast can never be retired (OQ-1, OQ-2, OQ-5). *Mitigation*: coverage is a Phase 0 gate criterion; plan per SIM family.
- **R2 Counters and keys locked in Aircast**: without an export, the first in-house sends are rejected as replays (OQ-4, OQ-7). *Mitigation*: secure access and export rights at the Phase 0 gate; test export on sample ICCIDs.
- **R10 Counter divergence**: both platforms send to the same cards. *Mitigation*: per-ICCID ownership flag and a single sender per card (ADR-3).
- **R11 Sleepy reachable by third parties**: at MSL 0, any SMS-PP to TAR "SLY" reaches the applet. *Mitigation*: the SMS firewall admits PID 0x7F only from the authorized origins (OQ-8); size the exposure by counting SIMs with Sleepy (OQ-3).
- **R13 Blocked at the finish line**: Phases 1–4 deliver but Phases 5 and 6 wait on parties who never deliver, leaving Nuevatel more dependent on Aircast. *Mitigation*: fallback decided at the Phase 0 gate; pivot checkpoint at the end of Phase 2.

**Standing risks:**

- **Plaintext exposure** (OQ-10): output files sit in plaintext in a cloud-synced folder; remediation is the first action of Phase 0.
- **Contract tension**: Mobiera's July 2022 email states that there is no dependency and that Nuevatel keeps the keys and control. Yet the Sleepy key sits with Mobiera and the counters sit in Aircast. Legal review is needed before Phase 2 (Aircast driver).

## Open Questions

1. **Coverage**: what share of active SIMs has a valid, current output file, per lot?
2. **Key validity**: were keys rotated after delivery, making the original output files obsolete?
3. **Sleepy**: what are its specification, proprietary security (key, algorithm, command format) and licensing terms? Which SIMs have it installed?
4. **Counters**: what validation mode does the profile use (greater-than vs exactly-plus-one)? Can Aircast export counters and key copies per ICCID? What is the reset policy?
5. **Master key**: does the manufacturer derive keys from a master key, and who holds it?
6. **S@T Browser**: what is its TAR, and what do MSL parameter 01 / data 02 mean on profile 15.03?
7. **Mobiera contract**: what is its current status, given that the prior contract expired in July 2022? What rights does Nuevatel have to Aircast, the counters and the key copy?
8. **SMSC**: what is its capacity (TPS)? What SMPP connectivity is available? Can the SMS firewall filter OTA traffic by TAR as well as by PID and origin, and which origins are authorized while Aircast and Nuevatel coexist?
9. **Team**: build, hire or partner for Java Card, OTA cryptography and HSM operations?
10. **Plaintext remediation**: who owns it, and by when?
11. **Stakeholders**: who are the business owner, the platform operators and the key custodians? Who approves the gates?
12. **Business case**: what do the Sleepy revenue share and Aircast cost, and what is the budget? None of these were provided.
13. **ATT**: what are the specific regulatory requirements for mass SIM messaging and subscriber data?
14. **Timeline**: are there target dates or deadlines? None were provided.
15. **Manufacturer request**: has the request for the new lot been sent, and when is a response expected?
16. **HSM**: is an HSM available, and does it support 3DES? What are the procurement lead time and budget? On-premises or managed?
17. **Device mix**: what data exists on the handsets active on the network, to build the test matrix from?
18. **Coverage threshold**: what share of the reachable base justifies building the in-house engine, rather than keeping Aircast for existing lots and owning only new ones?
19. **Aircast consumers**: which systems call the Aircast API directly today?
20. **OTA algorithms**: which KIC/KID algorithms and modes does each profile use for RAM and RFM, and does the HSM support them?
21. **Identity source**: which system is authoritative for the ICCID-to-IMSI mapping (provisioning or HLR/HSS)?
22. **Key rotation**: which key-rotation command do the cards accept?
23. **S@T push specification**: can Nuevatel obtain TCA S@T 01.20, 01.21, 01.22 and 01.23?
24. **Counter recovery**: how is a card's counter resynchronized after an uncertain send, especially if the profile requires exactly-plus-one?
25. **Plaintext exposure**: who could access the plaintext output files, since when, and do copies exist in version history, backups or synced devices?
