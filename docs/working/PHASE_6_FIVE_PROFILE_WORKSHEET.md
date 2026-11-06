# Phase 6: five independently labelled profiles

Status: **DRAFT. Lookups filled 2026-11-03, awaiting maintainer review. Not frozen.** This is a worksheet, not an evaluation dataset. The maintainer supplies five synthetic cases and expected outcomes from cited sources before seeing engine output. No model-written case or label may be marked human-authored. Keep real identifying details out of the repository.

Authorship split for this draft: the case design, facts, verdict logic and labels are the maintainer's (draft text of 2026-11-03). The model filled only the `[LOOKUP]` values, the programme slugs, the request parameters and the citations, from official pages read on 2026-11-03, and recorded every place where a published rule forced a change to the maintainer's facts (table below). The model did not open `data/eligibility/rules/`, the engine or any engine output. It used the verified records, cached pages and live official pages only.

Use [the coverage matrix](../PHASE_6_RULE_COVERAGE.md) and official evidence. Criterion labels are `meets`, `does_not_meet`, `unknown`, `not_published`. Headlines are `meets_checked_published_requirements`, `does_not_meet_published_requirements`, `needs_information_or_review`, or `not_covered`. Keep academic, document/deadline readiness and finance outcomes separate. A university-review judgment is not a numeric failure. `not_published` means the programme page is silent; it is never counted as passed and never counted as "not required".

Freeze each label set with an authorship note and date before the first engine run. If a disagreement later reveals a source error or ambiguous interpretation, preserve the original label and record the reviewed change and reason. The five cases are reported separately from the 35 assisted cases; a shared implementation and label author is not independent evidence.

## Request parameters (proposed; the request owns these)

Same for all five: country Germany; intake winter semester 2027/28; starting year 2027; `as_of` 2026-11-03 (the date the sources below were read; every deadline and amount is the value the page showed on that date). Page deadlines carry no year on some pages (KIT); they are applied to 2027 as published.

## Sources (all accessed 2026-11-03 unless stated)

| Id | Page | What it supplies |
|---|---|---|
| S1 | TU Berlin dates and deadlines, https://www.tu.berlin/en/go167, section "For master's programs", winter 2027/28 table | Open-admission master's: 01.06.2027 to 31.08.2027. Foreign-degree applicants have the same deadlines and need a VPD from uni-assist. Dates "published subject to amendment". |
| S2 | TU Berlin CS M.Sc. programme page, https://www.tu.berlin/en/studying/study-programs/all-programs-offered/study-course/computer-science-informatik-m-sc (registry `de/tub/cs-msc/programme`, cached 2026-10-05) | "Admission: Open admission"; 36 CP foundations (12 theoretical, 12 computer engineering or IT, 12 methodological-practical); 18 CP mathematics; at least 30 further CP in computer science, thesis excluded; English B2. No first-degree length or ECTS total is stated. |
| S3 | TU Berlin CS M.Sc. application page, https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission (`de/tub/cs-msc/application`, cached 2026-10-05, re-read live) | "The responsible examination board decides on the equivalence and the subject-specific qualification." Suitability Assessment Form mandatory unless the bachelor's was at TU Berlin. "There is no preliminary check of the documents." Foreign degree: VPD requested from uni-assist for TU Berlin. |
| S4 | Faculty IV English proficiency table, https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/english-proficiency-fac-iv-masters-programs (last update on page: 09/2024) | "IELTS Academic: Overall band score >= 6.5 points." No component minimum. Degree-based proof only for "native English" countries (India is not one). |
| S5 | Faculty IV application FAQ, https://www.tu.berlin/en/eecs/academics-teaching/study-offer/application-admission-faq (`de/tub/eecs-application-faq`) | IELTS overall 6.5 required even if 5.5 certifies B2; no validity restriction on English certificates; no conditional or provisional admission for foreign qualifications; documents after the deadline are not accepted; professional experience and the bachelor's thesis are not credited. |
| S6 | TU Berlin entry regulations M.Sc. CS, English reading version (unofficial, 2018), https://www.static.tu.berlin/fileadmin/www/10000040/1_Studium_Lehre/1_Studienangebot/2_Masterstudiengaenge/2_M_CS/Reading_Version_ZO_MSc_ComputerScience_Informatik__EN.pdf, sections 3 and 4 | Entry requirements are the element list plus English B2. The examination board votes on professional qualification and equivalence. No length or ECTS total of the first degree. |
| S7 | German Mission India, student visa page, https://india.diplo.de/in-en/service/2756350-2756350 (page dated 16.02.2026; `de/rules/embassy-india-studies-visa`) | Blocked account "to cover the first year of studies, currently amounting to 11,904.-- EUR", at most 992 EUR per month withdrawable. Proofs are listed "by one of the following means": blocked account, Verpflichtungserklaerung, "proof of a German or EU scholarship or stipend", education loan. No statement on combining proofs. APS certificate "almost always" required for admission with Indian degrees; exempt for "a stipend from EU or German public funds". |
| S8 | Federal Foreign Office, blocked account, https://www.auswaertiges-amt.de/en/sperrkonto-388600 | "The blocked account must have sufficient credit ... (unless other proof of financial support is presented in addition)." The amount depends on the purpose of stay and the competent mission. |
| S9 | Federal Foreign Office, studying FAQ, https://www.auswaertiges-amt.de/en/visa-service/buergerservice/faq/606850-606850 | Funding proof also satisfied by "a scholarship from public funds or a scholarship from an organization recognized in Germany". No amount. |
| S10 | KIT Computational and Data Science M.Sc., https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php (live; page dated 11.09.2026) | Non-EU deadline July 15 (winter), January 15 (summer); limited capacity: no. At least 3-year regular period and at least 180 ECTS; 20 LP basic mathematics; at least 40 LP in one of three areas and at least 12 LP in each other; bachelor thesis at least 6 LP; up to 12 LP missing: committee may admit with conditions at its discretion. English: degree with English as sole language of instruction and examination, "clearly stated in the Diploma Supplement, Transcript of Records or in the degree certificate"; or IELTS 6.5 with no section below 5.5; proof by end of enrolment. No GRE/GATE mentioned. |
| S11 | KIT Computer Science M.Sc., https://www.sle.kit.edu/english/vorstudium/master-computer-science.php (live; page dated 28.10.2026) | Non-EU deadline June 15 (winter), January 15 (summer). GRE (V151, Q164, AW4) not needed if the degree is from EHEA or a Lisbon state, or with a successful GATE (CS and IT, or Data Science and AI). Selection: GATE, or direct credits (theory 15, practical 30, computer engineering 8, mathematics 25), or an aptitude interview (three of four areas at 15/20/6/20). Bachelor's "completed within a standard period of study of at least three years and with a minimum number of 180 ECTS". B2 English by end of enrolment. |
| S12 | KIT informatics admission page, https://www.informatik.kit.edu/english/14346.php (`de/kit/cs-msc/admission`, cached 2026-10-16) | "All applicants, with a Bachelor Degree from a country not part of the Lisbon convention ... must submit a current GRE certificate (or GATE certificate)." GRE not older than 5 years, GATE 3 years. |
| S13 | KIT International Students Office, master application, https://www.intl.kit.edu/istudies/9074.php (page dated 02.10.2026) | "If not graduated yet please submit enrolment certificate with expected date of completition." Transcript with credit information, module descriptions. "Applicants from China, Vietnam and India are required to enclose the original APS-certificate in their application." |
| S14 | uni-assist, India country notes, https://www.uni-assist.de/en/tools/info-country-by-country/details-country/country/in/ | Documents must show the maximum and the minimum grade needed for the award of the degree, not the minimum for single courses. uni-assist converts grades to the German system (https://www.uni-assist.de/en/faqs/get-information/). |
| S15 | Council of Europe Lisbon Convention list, https://www.coe.int/en/web/conventions/full-list?module=signatures-by-treaty&treatynum=165, via `data/eligibility/country_groups.json` (fetched 2026-10-29, human-reviewed) | India is not a party. |

Grade conversion: no programme used here publishes a grade conversion rule or a grade cutoff. No official page I could open names the modified Bavarian formula; uni-assist says it converts with the degree's best and lowest passing grade, which is the same inputs. The converted values below (2.25, 2.6, 1.8) therefore use the maintainer's stated rule, `1 + 3 x (best - obtained) / (best - passing)`, and are informational only: no criterion in these cases compares against them.

## Changes to the maintainer's facts that a published rule forced

| Case | Maintainer text | Change | Why |
|---|---|---|---|
| H01, H02, H05 | "each component >= [LOOKUP: min component]" | TU Berlin publishes no component minimum. Components are still given; the component row is `not_published`. | S4. |
| H01, H02, H05 | "absent: none required by programme" | Added to "available": Suitability Assessment Form, uni-assist VPD, APS certificate. | S3 requires the form and the VPD. S7 says APS is almost always needed for Indian degrees; TU Berlin does not publish APS itself. Without them readiness would not be "ready". |
| H01, H02, H05 | "GRE: verdict meets only if the programme says GRE is not required" | TU Berlin is silent about GRE and GATE. Row is `not_published`, not `meets`. Case not set aside, because nothing requires GRE. | S2, S3. |
| H05 | "equivalence assessment requested, pending" and "[LOOKUP: required years/ECTS]" | TU Berlin has no length or ECTS minimum and no advance assessment. The degree row is the equivalence of the first degree, decided by the examination board after application. | S3, S5, S6. |
| H03 | "Grade ... unknown" | KIT CS publishes no grade cutoff. The grade row is `not_published`; only the top-10% rank on the interview route is `unknown`. | S11. |
| H04 | "170 Indian university credits", "project 14 credits", "medium-of-instruction certificate issued by the university" | KIT CDS tests total ECTS (180), thesis in LP (6) and wants English instruction stated in the Diploma Supplement, transcript or degree certificate. Added: the Diploma Supplement gives ECTS-equivalents (total 240, project 20) and states English as sole language of instruction and examination. | S10. Without these the ECTS rows would be `unknown` on a unit mismatch, and a stand-alone certificate is not a listed proof. |
| H04 | "funds ... [LOOKUP: whether the source accepts this route]" | Scholarship made German public-funds type (DAAD-style), amounts set so the total equals the required sum. Verdict `unknown`. | S7 to S9. |

## H01

- Status: draft, lookups filled 2026-11-03; pending maintainer review and freeze
- Profile author / label author / reviewer: maintainer (facts and labels, draft); model filled lookups and citations; reviewer: (none yet)
- Related base case (if any): none (base for H05)
- Target programme slug / country / intake / starting year / as_of: `tu-berlin-m-sc-computer-science` / Germany / winter semester 2027/28 / 2027 / 2026-11-03
- Citizenship(s), degree country, school country, relevant enrolment/residence: India; degree country India; school country India; resident in India, not enrolled elsewhere
- Degree, institution, duration, completion and total credits/unit: B.Tech Computer Science, synthetic Indian university, 4 years (8 semesters), completed, 160 Indian university credits (unit: university credits, not ECTS). TU Berlin publishes no total-credit or length minimum, so the total is carried as a fact only.
- Confirmed subject allocations, thesis credits, university equivalence/assessment: transcript mapping to TU Berlin's areas, in credit points: mathematics 18 (exactly the minimum of 18 CP); theoretical computer science 14, computer engineering or IT 13, methodological-practical 20 (foundations 47 against 36, each area above 12); further computer science excluding the thesis 36 (against 30); bachelor project 12 credits, not counted. No university equivalence assessment on file: TU Berlin offers none in advance ("no preliminary check of the documents", S3).
- Original grade/scale/best/passing, official conversion/provenance, class rank: CGPA 7.5 / scale 10 / best 10 / passing 4 (degree-award minimum, as uni-assist asks, S14); stated rule gives 2.25 = 1 + 3 x (10 - 7.5) / (10 - 4); TU Berlin prescribes no conversion and no grade cutoff; no class rank supplied
- Language tests (identity, scale version, date, overall/components), education proof: IELTS Academic, band scale 0-9, taken 2026-09-14 (TU Berlin has no validity limit, S5), overall 6.5 exactly; components L 7.0, R 6.5, W 6.0, S 6.5 (TU Berlin sets no component minimum); no medium-of-instruction certificate
- GRE scores/percentiles/date; GATE paper/year/qualification; interview/exam outcome: GRE not taken (none, not "not supplied"); GATE none; no interview or exam outcome
- Available, absent and pending documents: available: degree certificate, transcript, passport copy, IELTS report, CV, Suitability Assessment Form, uni-assist VPD for TU Berlin, APS certificate; absent: none; pending: none
- EUR funds / period / proof route; other relevant facts: blocked account with 11,904 EUR (first-year amount, S7); proof route blocked account; funded for 12 months
- Expected academic headline / unresolved reasons: meets_checked_published_requirements / none. Surfaced separately, not counted as passed: no component minimum, no grade cutoff, no GRE or GATE rule is published.
- Expected criteria (fact → requirement → applicability/verdict/margin/citation/rationale):
  - Language overall: IELTS overall 6.5 → overall >= 6.5 → applies / meets / margin 0.0 / S4, S5 / boundary equality counts as meeting
  - Language components: L 7.0, R 6.5, W 6.0, S 6.5 → no component minimum published → applies / not_published / n/a / S4 / the page states the overall score only
  - Language validity: test date 2026-09-14 → no validity restriction → applies / meets / n/a / S5 / "currently" no restriction; page says it may change
  - Subject area, mathematics: 18 CP → at least 18 CP → applies / meets / margin 0 / S2, S3 / boundary equality
  - Foundations of computer science: 47 CP (14 / 13 / 20) → 36 CP with 12 in each of three areas → applies / meets / margin +11 total, +2, +1, +8 / S2, S3 / theory credits taken only from modules the faculty recognises as theoretical
  - Further computer science, thesis excluded: 36 CP → at least 30 CP → applies / meets / margin +6 / S2, S5 / the 12-credit project is not counted
  - Degree field: B.Tech Computer Science, completed → first professionally qualifying degree in computer science or a closely related programme → applies / meets / n/a / S3 / the board's equivalence vote is routine process once the element list is confirmed (R01); no length minimum exists to compare
  - Final grade: 2.25 converted → no minimum grade published → applies / not_published / n/a / S2, S3 / informational only
  - GRE and GATE: none → no entrance-test rule published → applies / not_published / n/a / S2, S3 / silent page is not "GRE not required"
- Expected readiness and finance outcomes: readiness: documents complete (including form, VPD, APS); window for winter 2027/28 is 01.06.2027 to 31.08.2027 (S1); as_of 2026-11-03 is before it opens, so no deadline is passed → ready; finance: meets (11,904 EUR against the 11,904 EUR first-year amount, margin 0 EUR, S7)
- Labels frozen on (before engine output):
- First engine comparison and any reviewed label changes (later):

## H02

- Status: draft, lookups filled 2026-11-03; pending maintainer review and freeze
- Profile author / label author / reviewer: maintainer (facts and labels, draft); model filled lookups and citations; reviewer: (none yet)
- Related base case (if any): none
- Target programme slug / country / intake / starting year / as_of: `tu-berlin-m-sc-computer-science` / Germany / winter semester 2027/28 / 2027 / 2026-11-03. Same programme as H01 on purpose: it is the only covered programme that publishes a mathematics minimum, has no total-ECTS minimum and no GRE or GATE rule for an Indian degree. KIT CS needs GRE or GATE; KIT CDS has a 180-ECTS total and a 12-LP discretion band that would make a 6-credit shortfall a review matter.
- Citizenship(s), degree country, school country, relevant enrolment/residence: India; degree India; school India; resident in India
- Degree, institution, duration, completion and total credits/unit: B.E. Electronics and Communication, synthetic Indian university, 4 years, completed, 168 Indian university credits
- Confirmed subject allocations, thesis credits, university equivalence/assessment: in credit points by transcript mapping: mathematics 12 (the 18 CP minimum minus 6); theoretical computer science 14, computer engineering or IT 20, methodological-practical 16 (foundations 50, each area above 12); further computer science excluding the thesis 34; project 10 credits, not counted; no university equivalence assessment (none offered in advance, S3)
- Original grade/scale/best/passing, official conversion/provenance, class rank: percentage 68% / scale 100 / best 100 / passing 40; stated rule gives 2.6 = 1 + 3 x (100 - 68) / (100 - 40); TU Berlin prescribes no conversion; no class rank
- Language tests (identity, scale version, date, overall/components), education proof: IELTS Academic, band scale 0-9, taken 2026-08-22, overall 7.0 (+0.5 over 6.5); components L 7.5, R 7.0, W 6.5, S 7.0
- GRE scores/percentiles/date; GATE paper/year/qualification; interview/exam outcome: GRE and GATE none; no interview
- Available, absent and pending documents: all standard documents available: degree certificate, transcript, passport copy, IELTS report, CV, Suitability Assessment Form, uni-assist VPD, APS certificate
- EUR funds / period / proof route; other relevant facts: blocked account with 11,904 EUR, 12 months
- Expected academic headline / unresolved reasons: does_not_meet_published_requirements / mathematics credit shortfall only
- Expected criteria (fact → requirement → applicability/verdict/margin/citation/rationale):
  - Maths credits: 12 CP → at least 18 CP → applies / does_not_meet / margin -6 CP / S2, S3 / clear numeric shortfall, not a review matter; no discretion band is published for TU Berlin; S5: "you will only be admitted if you meet all the requirements in full"
  - Language: IELTS 7.0 → overall >= 6.5 → applies / meets / margin +0.5 / S4 / —
  - Language components: all given → no component minimum published → applies / not_published / n/a / S4 / —
  - Foundations of computer science: 50 CP (14 / 20 / 16) → 36 CP with 12 in each area → applies / meets / margin +14 total, +2, +8, +4 / S2, S3 / —
  - Further computer science, thesis excluded: 34 CP → at least 30 CP → applies / meets / margin +4 / S2 / —
  - Degree field: B.E. Electronics and Communication → computer science or a closely related programme → applies / meets / n/a / S2, S3 / judgment call: counted as "closely related" because the published test is the element list. If you prefer every non-CS degree to be board-decided, this row becomes `unknown` and the headline does not change
  - Final grade: 2.6 converted → no minimum grade published → applies / not_published / n/a / S2, S3 / informational
  - GRE and GATE: none → no rule published → applies / not_published / n/a / S2, S3 / —
- Expected readiness and finance outcomes: readiness: documents complete, window 01.06.2027 to 31.08.2027 not passed (S1) → ready (readiness is separate from the academic failure); finance: meets (11,904 EUR, margin 0 EUR, S7)
- Labels frozen on (before engine output):
- First engine comparison and any reviewed label changes (later):

## H03

- Status: draft, lookups filled 2026-11-03; pending maintainer review and freeze
- Profile author / label author / reviewer: maintainer (facts and labels, draft); model filled lookups and citations; reviewer: (none yet)
- Related base case (if any): none
- Target programme slug / country / intake / starting year / as_of: `kit-m-sc-computer-science` / Germany / winter semester 2027/28 / 2027 / 2026-11-03. Chosen because its GRE-or-GATE rule applies to an Indian degree (India is not a Lisbon party, S12, S15), which makes "GRE none, GATE not supplied" a real unknown.
- Citizenship(s), degree country, school country, relevant enrolment/residence: India; degree India; school India; resident in India
- Degree, institution, duration, completion and total credits/unit: B.Tech Information Technology, synthetic Indian university, 4 years, final semester in progress, total credits NOT SUPPLIED
- Confirmed subject allocations, thesis credits, university equivalence/assessment: not supplied
- Original grade/scale/best/passing, official conversion/provenance, class rank: CGPA 8.1 / scale 10 / best 10 / passing: not supplied; conversion: not supplied; class rank: not supplied
- Language tests (identity, scale version, date, overall/components), education proof: language test NOT SUPPLIED (not "none"; the applicant says a test is planned but gave no details)
- GRE scores/percentiles/date; GATE paper/year/qualification; interview/exam outcome: GRE: none (confirmed not taken); GATE: not supplied; interview: not supplied
- Available, absent and pending documents: available: passport copy, CV; pending: final transcript and degree certificate (degree not yet awarded; KIT accepts an enrolment certificate with expected completion date at application, S13); absent: language certificate; not supplied: APS certificate (KIT requires the original with the application for Indian applicants, S13), module descriptions
- EUR funds / period / proof route; other relevant facts: funds not supplied
- Expected academic headline / unresolved reasons: needs_information_or_review / language test unknown; GATE unknown with GRE confirmed none; credits and subject allocations unknown; degree completion pending
- Expected criteria (fact → requirement → applicability/verdict/margin/citation/rationale):
  - Language: not supplied → B2 proof, IELTS 6.5 with no section below 5.5, or an English-only degree stated in the Diploma Supplement, transcript or certificate; due "by the end of the enrollment period at the latest" → applies / unknown / n/a / S11 / fact missing, not a failure; KIT allows provisional evidence at application
  - Degree completion and total credits: final semester in progress, total not supplied → bachelor's completed in at least 3 years with at least 180 ECTS → applies / unknown / n/a / S11, S13 / enrolment certificate is accepted at application; whether admission is then conditional on the final certificate is not stated, so no verdict from the page alone
  - Subject allocations: not supplied → direct route theory 15, practical 30, computer engineering 8, mathematics 25 CP; or successful GATE; or aptitude interview with three of four areas at 15/20/6/20 → applies / unknown / n/a / S11 / nothing supplied for any route; do not infer an outcome
  - Grade: CGPA 8.1, passing mark not supplied → no minimum grade published → applies / not_published / n/a / S11 / informational; conversion could not be done without the degree-award passing mark (S14), and the grade only feeds the selection ranking (up to 70 of 190 points), which is not an eligibility criterion
  - Top-10% rank: not supplied → proof of being in the best 10% of the year, interview route only → applies only if the interview route is used / unknown / n/a / S11, S12 / route not yet determined
  - GRE: none (confirmed); GATE: not supplied → GRE (V151, Q164, AW4) or GATE in CS and IT or Data Science and AI, required for a degree from a country outside the Lisbon group → applies (India is outside it) / unknown / n/a / S11, S12 / GRE is absent, but GATE could still satisfy the "one of"; unknown, not a failure
- Expected readiness and finance outcomes: readiness: not ready; documents pending (transcript, certificate), absent (language proof) and not supplied (APS); deadline June 15, 2027 (S11) not passed; finance: unknown (funds not supplied)
- Labels frozen on (before engine output):
- First engine comparison and any reviewed label changes (later):

## H04

- Status: draft, lookups filled 2026-11-03; pending maintainer review and freeze
- Profile author / label author / reviewer: maintainer (facts and labels, draft); model filled lookups and citations; reviewer: (none yet)
- Related base case (if any): none
- Target programme slug / country / intake / starting year / as_of: `kit-m-sc-computational-and-data-science` / Germany / winter semester 2027/28 / 2027 / 2026-11-03. Its page publishes the exemption: a degree with English as sole language of instruction and examination is "sufficient proof" (S10). TU Berlin, Saarland and Stuttgart do not accept that route for an Indian degree; KIT CS also needs GRE or GATE.
- Citizenship(s), degree country, school country, relevant enrolment/residence: India; degree India; school India; resident in India
- Degree, institution, duration, completion and total credits/unit: B.Tech Computer Science, synthetic Indian university, 4 years, completed, 170 Indian university credits; the university's medium of instruction was English; the Diploma Supplement gives the ECTS-equivalent: total 240 ECTS
- Confirmed subject allocations, thesis credits, university equivalence/assessment: in LP by transcript mapping: basic mathematics (linear algebra and analysis or higher mathematics) 28 (minimum 20); computer science 62 (main area, minimum 40); applied mathematics 18 (minimum 12); engineering sciences (electrical engineering and information technology) 16 (minimum 12); bachelor project 14 Indian credits = 20 ECTS on the Diploma Supplement (minimum 6 LP); no university equivalence assessment on file
- Original grade/scale/best/passing, official conversion/provenance, class rank: CGPA 8.4 / scale 10 / best 10 / passing 4; stated rule gives 1.8 = 1 + 3 x (10 - 8.4) / (10 - 4); KIT CDS publishes no grade cutoff and has no limited capacity; no class rank
- Language tests (identity, scale version, date, overall/components), education proof: no language test taken (none, deliberate); education proof: medium-of-instruction certificate issued by the university, and the Diploma Supplement and transcript state English as the sole language of instruction and examination
- GRE scores/percentiles/date; GATE paper/year/qualification; interview/exam outcome: GRE none; GATE none; no interview
- Available, absent and pending documents: all standard documents (degree certificate, transcript, Diploma Supplement, module descriptions, passport copy, CV, APS certificate) plus the medium-of-instruction certificate
- EUR funds / period / proof route; other relevant facts: DAAD-style scholarship (German public funds), award letter for 992 EUR per month for 6 months = 5,952 EUR, plus a blocked account of 5,952 EUR; total 11,904 EUR, equal to the first-year amount
- Expected academic headline / unresolved reasons: meets_checked_published_requirements / none. The exemption is automatic with the stated proof (S10); nothing is left to a university decision.
- Expected criteria (fact → requirement → applicability/verdict/margin/citation/rationale):
  - Language test: none → IELTS 6.5 with no section below 5.5, or another listed test → test route not used; alternative route applies / meets via exemption / n/a / S10 / the exemption is an alternative, not a test shortfall
  - Education proof: Diploma Supplement and transcript state English as sole language of instruction and examination → "clearly stated in the Diploma Supplement, Transcript of Records or in the degree certificate" → applies / meets / n/a / S10 / the separate medium-of-instruction certificate is extra; it is not one of the listed proofs
  - Degree length and ECTS: 4 years; 240 ECTS on the Diploma Supplement → at least 3 years and at least 180 ECTS → applies / meets / margin +1 year, +60 ECTS / S10 / —
  - Basic mathematics: 28 LP → at least 20 LP → applies / meets / margin +8 / S10 / —
  - Subject areas: computer science 62, applied mathematics 18, engineering sciences 16 → at least 40 in one area and at least 12 in each of the other two → applies / meets / margin +22, +6, +4 / S10 / —
  - Bachelor thesis: 20 ECTS-equivalent → at least 6 LP → applies / meets / margin +14 / S10 / —
  - Final grade: 1.8 converted → no minimum grade published → applies / not_published / n/a / S10 / informational
  - GRE and GATE: none → no rule published for this programme → applies / not_published / n/a / S10 / silent page is not "GRE not required"
- Expected readiness and finance outcomes: readiness: ready, the certificate and Diploma Supplement count as complete; deadline July 15, 2027 for non-EU applicants (S10) not passed; finance: unknown. S8 says a blocked account may be partial "unless other proof of financial support is presented in addition", and S7 and S9 accept a German or EU public scholarship, but S7 lists the proofs as alternatives, states no rule for combining them and no share of the amount a scholarship must cover. The mission decides; kept separate from the academic headline.
- Labels frozen on (before engine output):
- First engine comparison and any reviewed label changes (later):

## H05

- Status: draft, lookups filled 2026-11-03; pending maintainer review and freeze
- Profile author / label author / reviewer: maintainer (facts and labels, draft); model filled lookups and citations; reviewer: (none yet)
- Related base case (if any): H01 (same slug `tu-berlin-m-sc-computer-science`, same language, grade and finance facts; only the degree duration, equivalence status and funds differ)
- Target programme slug / country / intake / starting year / as_of: `tu-berlin-m-sc-computer-science` / Germany / winter semester 2027/28 / 2027 / 2026-11-03
- Citizenship(s), degree country, school country, relevant enrolment/residence: same as H01
- Degree, institution, duration, completion and total credits/unit: B.Sc. Computer Science, synthetic Indian university, 3 years (6 semesters), completed, 120 Indian university credits
- Confirmed subject allocations, thesis credits, university equivalence/assessment: required subject areas meet the minimum, same CP values as H01 (mathematics 18, foundations 47 with 14 / 13 / 20, further computer science 36). TU Berlin publishes no required length or ECTS total of the first degree (S2, S3, S6), only "a first professionally qualifying degree ... or equivalent foreign university degree", and the examination board decides equivalence after application. No advance equivalence assessment exists (S3, S5), so none is on file or pending.
- Original grade/scale/best/passing, official conversion/provenance, class rank: same as H01 (2.25 informational)
- Language tests (identity, scale version, date, overall/components), education proof: same as H01 (IELTS Academic overall 6.5, taken 2026-09-14)
- GRE scores/percentiles/date; GATE paper/year/qualification; interview/exam outcome: same as H01
- Available, absent and pending documents: all documents available, as in H01 (VPD issued); the board's equivalence vote cannot exist before the application
- EUR funds / period / proof route; other relevant facts: blocked account with 10,904 EUR, i.e. the 11,904 EUR first-year amount (S7) minus 1,000 EUR, a small shortfall
- Expected academic headline / unresolved reasons: needs_information_or_review / equivalence of a 3-year, 120-credit degree to a first professionally qualifying degree is for the examination board to decide after application (a review judgment, not a numeric failure; no length minimum is published)
- Expected criteria (fact → requirement → applicability/verdict/margin/citation/rationale):
  - Degree equivalence: 3 years / 120 credits → first professionally qualifying degree in computer science or a closely related programme, "German or equivalent foreign university degree"; no length or ECTS minimum published → applies / unknown / n/a / S3, S6 / the board decides equivalence; do not mark does_not_meet
  - Language, grade, subject areas, entrance tests: as H01 → meets (language overall, margin 0.0; mathematics, margin 0; foundations; further computer science), not_published (components, grade, GRE/GATE), same margins as H01
- Expected readiness and finance outcomes: readiness: ready apart from the pending decision; window 01.06.2027 to 31.08.2027 not passed (S1); finance: does_not_meet (10,904 EUR against 11,904 EUR, margin -1,000 EUR, S7), kept separate from the academic headline
- Labels frozen on (before engine output):
- First engine comparison and any reviewed label changes (later):
