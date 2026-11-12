# Gold set review (model pass)

Human acceptance recorded 2026-10-27: the maintainer accepted all 104 retained
items and the following targeted updates. Authorship remains `model`; the
current dataset records `reviewed_by: human`. The historical model pass below
is preserved, including its uncertainty notes; acceptance does not make the
review independent or remove the known label ambiguity.

- b09 / c19: specify a qualifying university degree obtained outside Germany.
- b10: ask for winter 2026/27 regular on-campus fees; label the current
  contribution source (EUR 361), replacing the approximate FAQ estimate.
- c05: include both the department page and January 2026 accepted-proof PDF;
  retain earlier TOEFL 95 / IELTS 7.0 and add the PDF's 2026 TOEFL threshold.

Reviewed: `evaluation/datasets/gold_qa.jsonl` against the page text in `data/processed/chunks.jsonl`. Local files only. Every item was checked for the right label, a supported hint, no page echo, the right kind and valid labels. Refusal topics were searched across all 72 docs.

## Summary

| | Count |
|---|---|
| Items reviewed | 107 |
| Kept unchanged | 81 |
| Fixed | 23 |
| Dropped | 3 |
| **Final items** | **104** |

Final count per kind: requirement 45, country_rules 24, confusable 11, multi_hop 10, refusal 9, coverage 5.

`scripts/validate_gold.py` passes (104 items ok). `reviewed_by` stays "model" on every item.

Most common problem: a second doc stated the same fact, so a single-doc label would undercount recall. Several sources overlap. TUM programme pages repeat the department pages. KIT's CS programme page repeats its admission page. Saarland's programme pages repeat its application guide. TU Berlin's suitability form repeats the application page. Each affected item was reworded so that only the labelled doc answers it, or it was dropped.

## Per-item results

| qid | kind | status | note |
|---|---|---|---|
| a01 | requirement | ok | GRE for India degrees (Q 164, AW 4.0, verbal ignored, GATE CS alternative) is on the informatics department page. |
| a02 | requirement | ok | Visa applicants are advised Feb 1 to Mar 31; the compulsory winter deadline is May 31. Department page only. |
| a03 | requirement | ok | Student fees 97.00 € and the semester fee paid on top of tuition are on the informatics programme page. |
| a04 | requirement | ok | 90-min test, 20-30 questions, four topic areas, 20 Aug 2026. |
| a05 | requirement | ok | APS for China/India/Vietnam is on the DEA department page. |
| a06 | requirement | ok | 6,000 euros per semester and the waivers line are on the DEA programme page. |
| a07 | requirement | fixed | The DEA programme page also lists the application documents. The question now asks for the statement length (max 2 pages) and essay length (~1,000 words), which only the department page gives. |
| a08 | requirement | ok | Non-EU degree: GRE QR > 75th, VR > 15th percentile, AW 3.5, otherwise denied. |
| a09 | requirement | fixed | `rwth/master-application-international` also gives the Mar 1 / Sep 1 deadline. The question now asks for the opening dates (Dec 1 / Jun 1), which only the deadlines table gives. |
| a10 | requirement | ok | Section 3.2 competency areas and the examination board decision are on the department page. |
| a11 | requirement | ok | No TOEFL MyBest; a single session is required; results must be verifiable by the provider. |
| a12 | requirement | fixed | The degree subjects (CS/maths/physics) are also on `ds-msc/requirements` and `ds-msc/programme`. The question now asks about the module profiles and CP, which only the application page lists. |
| a13 | requirement | ok | Applicants for the March 1 deadline are usually not informed before May. |
| a14 | requirement | ok | Academic, not general, IELTS. Only the DS application page says this. |
| a15 | requirement | ok | Faculty IV FAQ: IELTS 6.5 overall even if 5.5 shows B2. |
| a16 | requirement | dropped | The theory-credit rule (discrete maths/algorithms do not count, 12 CP TCS) is stated in full on both `tub/cs-msc/application` and `tub/cs-msc/suitability-form`. No detail is unique to one of them. |
| a17 | requirement | ok | VPD from uni-assist from summer 2026 is on the application page. |
| a18 | confusable | ok | Five informatics essay topics; DEA lists three different topics. |
| a19 | confusable | ok | Three DEA essay topics; checked against the informatics list. |
| a20 | confusable | ok | Informatics is part-time possible with proportional tuition; DEA is full-time only (both DEA pages). |
| a21 | confusable | ok | CS needs German and English to enrol; DS is fully English with no German (`ds-msc/requirements`). |
| a22 | confusable | ok | DS waives the GRE for EU/EEA citizens and Bildungsinländer; CS keys on a non-EU first degree. |
| a23 | requirement | fixed | Kind changed from confusable. The language PDF marks both CS and DS with footnote 3 (an English bachelor's thesis can prove English), so the sibling does not differ. The DS contrast was removed from the hint. |
| b01 | requirement | ok | Saarland guide: GRE/GATE for non-EHEA/CH/UK degrees, no minimum score, home editions accepted. |
| b02 | requirement | ok | IELTS 7.0, TOEFL iBT 95, PTE 76; guide only. |
| b03 | requirement | dropped | The winter deadline (May 15, early Nov 15) is on both the CS programme page and the application guide. |
| b04 | requirement | fixed | The CS programme page also says "two academic references". The question now asks how letters are submitted (review forms by referees, no mailed letters), which only the guide gives. |
| b05 | requirement | ok | Original digitally signed APS for China/India/Vietnam; guide only. |
| b06 | requirement | ok | CGPA 75% or 3.00/4 plus top 10%; guide only. |
| b07 | requirement | fixed | "MOI not accepted" is on the DSAI page, the CS page and the guide. The question now covers home-edition and expired tests (guide only). The doc changed to `saarland/masters-application-guide`. |
| b08 | requirement | ok | TOEFL iBT 95 (new 5.0) or IELTS 7.0; aptitude page only. |
| b09 | requirement | fixed | `tud/cs-msc/programme` also gives the non-EU window. The question now also asks about the uni-assist route, which only the aptitude page names. |
| b10 | requirement | fixed | The programme label was set to null because the question names no programme. The fee (~360 €, not a tuition fee) was verified. |
| b11 | requirement | ok | Aptitude assessment document list verified. |
| b12 | requirement | ok | No German proof for English master's; A2 recommended. International FAQ. |
| b13 | requirement | fixed | GRE scores are on both the KIT programme and admission pages. The question now asks about the EHEA exemption, which only the programme page states. |
| b14 | requirement | ok | GRE not older than 5 years (GATE 3); admission page only. |
| b15 | requirement | ok | June 15 / January 15; admission page only. |
| b16 | requirement | ok | 100 places, 190-point ranking, 70 for the grade. |
| b17 | requirement | fixed | The programme label was set to null because the question names no programme. EUR 1,500 per semester was verified. |
| b18 | requirement | ok | IELTS 6.5 / no band below 5.5, TOEFL 90 on the CDS page. "computational and data science" is the programme name, not an echo. |
| b19 | requirement | ok | Bachelor thesis of at least 6 LP. |
| b20 | confusable | dropped | Maths 25 CP (and the other minimums) are stated identically on `kit/cs-msc/programme` and `kit/cs-msc/admission`. |
| b21 | confusable | ok | CDS: 20 LP basic maths plus 40/12 LP; CS asks 25 CP. |
| b22 | confusable | fixed | The interview route is also on the admission page. The question now leads with the GATE route, which only the programme page gives; the hint keeps the interview minimums. |
| b23 | confusable | ok | Up to 12 LP missing allows conditional admission within the first three semesters; CS uses an interview instead. |
| b24 | confusable | ok | Maschinenbau is listed for CDS; CS needs CS or essentially the same content. |
| c01 | requirement | ok | GATE ≥ 750, by Aug 20 / Feb 20; the guide holds the thresholds (programme pages give none). |
| c02 | requirement | ok | Grades/GPA are not used; 60 ECTS content match. |
| c03 | requirement | ok | Paper documents by July 15 / January 15; a postmark is not enough. |
| c04 | requirement | ok | At least 8 weeks after the complete application. |
| c05 | requirement | ok | C1, e.g. TOEFL iBT 95 or IELTS Band 7; department page only. |
| c06 | requirement | ok | Results on C@MPUS 6-7 weeks after the deadline; apply 9 months ahead. |
| c07 | requirement | ok | Semester fee EUR 184.00. |
| c08 | requirement | ok | The certificate must be uploaded; no direct send by TOEFL/ETS. |
| c09 | requirement | fixed | Kind changed from confusable. The AIML page states no specialisations at all rather than a different value. The sibling sentence was removed. |
| c10 | confusable | ok | AIML: R&D in basic research or industry; CS page: international career. |
| c11 | confusable | ok | Mirror of c10; both pages checked. |
| c12 | multi_hop | fixed | 992/11,904 appears in about ten docs, so the funds hop was ambiguous. It now asks about the Munich residence permit blocked account, and the second doc changed to `de/munich/residence-permit-study`. |
| c13 | multi_hop | ok | Stuttgart tuition 1500 EUR plus the Stuttgart residence permit (992 EUR/month). |
| c14 | multi_hop | ok | TUD requires APS for Indian certificates; the APS India graduate fee is 18,000 INR, non-refundable. |
| c15 | multi_hop | ok | Saarland requires the original signed APS; APS FAQ: do not rename or merge the PDF. |
| c16 | multi_hop | ok | TUM APS for India; `aps-india-home` names Engineering and SS 2027 and says the APS is issued only after the dMAT. |
| c17 | multi_hop | fixed | The KIT GRE minimums are on both the programme and admission pages. The KIT doc changed to `kit/cs-msc/admission`, and the question adds the 5-year validity, which only that page gives. |
| c18 | multi_hop | ok | TU Berlin IELTS 6.5 (EECS FAQ) vs Darmstadt IELTS 7.0 (guide). |
| c19 | multi_hop | ok | TUD non-EU window via uni-assist plus uni-assist's 8-week advice. |
| c20 | multi_hop | ok | TUM 97.00 € plus DAAD 120-130 €/month under 30. |
| c21 | multi_hop | fixed | The STEM scholarship page has the same 992 €/460 € figures. The question now names the "master studies (all disciplines)" programme. |
| d01 | country_rules | ok | 18,000 INR, non-refundable; the amount is only in the leaflet. |
| d02 | country_rules | ok | A low dMAT score does not mean automatic refusal. |
| d03 | country_rules | fixed | The TUD FAQ also gives "4-6 weeks" for uni-assist. The question now asks how incompleteness is reported and the deadline for missing documents, which only the uni-assist FAQ gives. |
| d04 | country_rules | ok | Six steps; fees in step 5 after the online application. |
| d05 | country_rules | ok | Duolingo, PTE and TOEFL home edition are not recognised for visas in India. |
| d06 | country_rules | ok | A rejection notice is enough to lift the blocking notice. |
| d07 | country_rules | ok | The Federal Foreign Office does not award scholarships directly; it funds intermediaries; foundations are listed. |
| d08 | country_rules | ok | 900-1,200 €/month; semester contribution 70-430 EUR. |
| d09 | country_rules | ok | 120-130 €/month under 30. |
| d10 | country_rules | ok | Passport with visa, letter of acceptance, statutory insurance. |
| d11 | country_rules | ok | English-taught programmes are exempt from the German requirement. |
| d12 | country_rules | ok | 33 months, or 21 with B1. |
| d13 | country_rules | ok | Chancenkarte for up to one year after employment ends. |
| d14 | country_rules | ok | Existing Master's degree means you cannot apply; the programme must be tuition-free. |
| d15 | country_rules | ok | One year in Germany within a home master's; credits must be recognised. |
| d16 | country_rules | ok | No repayment; 992 € for students. |
| d17 | country_rules | ok | 300 €/month (150 + 150); nationality and income are not considered. |
| d18 | country_rules | ok | Munich: register within one week. |
| d19 | country_rules | ok | Aachen: HiWi work does not count toward 140/280 days. |
| d20 | country_rules | ok | Berlin: 14 days, free of charge. |
| d21 | country_rules | ok | Online only; document list verified, including no foreign insurance. |
| d22 | country_rules | ok | Karlsruhe: permit invalid after 6 months abroad; inform the office. |
| d23 | country_rules | ok | Stuttgart: Fiktionsbescheinigung about a week before expiry; ~100 EUR fee if invited. |
| d24 | country_rules | fixed | The hint said "mainly by prior appointment" and gave the eligibility loosely. It now gives the page's conditions: appointment booking, Saarland residence and certain permit types. |
| d25 | refusal | ok | Admission chances; no source estimates them. |
| d26 | refusal | ok | No RWTH vs TU Berlin ranking in the corpus (the only rankings are Saarland's CHE mentions). |
| d27 | refusal | ok | No KIT acceptance rate (KIT only gives 100 places). TU Berlin's "<5%" does not apply. |
| d28 | refusal | ok | Netherlands not covered. |
| d29 | refusal | ok | UK not covered. |
| d30 | refusal | ok | Canada only appears in visa-exemption lists. |
| d31 | refusal | ok | US OPT/H-1B not covered. |
| d32 | refusal | ok | No salary figures (only "attractive salaries" on the KIT CDS page). |
| d33 | requirement | fixed | Was a refusal, but the Darmstadt guide states € 460/month for a shared-flat room (€ 395 Studierendenwerk). Converted to a requirement on `tu-darmstadt/informatics-master-admission-guide`, `expect_refusal` false. |
| d34 | refusal | ok | No flight content. |
| d35 | coverage | fixed | `university` "LMU Munich" is not a chunk label, so it was set to null. The university name stays in the question. |
| d36 | coverage | fixed | Same change: Bonn label set to null. |
| d37 | coverage | fixed | Same change: Tübingen label set to null. |
| d38 | coverage | fixed | Same change: Mannheim label set to null. |
| d39 | coverage | fixed | Same change: Heidelberg label set to null. |

## For the human pass

These are the items I am least sure about:

- **a21**: The RWTH language PDF row "Computer Science M.Sc. German & English" also answers the question, though tersely. The label is kept on `rwth/cs-msc/application`.
- **a23**: The same PDF's footnote 3 also covers the bachelor's thesis route for CS, which is a partial competing doc. Please also confirm the change of kind to requirement.
- **b09 / c19**: `tud/cs-msc/programme` still states the non-EU window; only the uni-assist part is unique to the aptitude page. Possible partial recall noise.
- **b13**: The KIT admission page implies the exemption through the Lisbon Convention list. The EHEA wording is only on the programme page.
- **b22**: Kept as confusable (GATE/interview route vs CDS conditional admission). Please check you agree that these are "the same field".
- **c10 / c11**: The career-orientation sentences are a soft confusable pair. Consider demoting one to requirement.
- **c16**: The dMAT rule is also described in `aps-india-leaflet-graduates-2026` and `aps-india-faqs`. Only `aps-india-home` names Engineering explicitly.
- **c17**: It now overlaps b14 on the 5-year GRE validity. That is acceptable for a multi_hop but worth a glance.
- **d09**: The Darmstadt guide gives a different student insurance range (125-150 €). The question is country-level, so the DAAD page stays the label.
- **d27**: Refusal is correct for KIT, but a model might wrongly cite TU Berlin's "<5% admitted". It is a good adversarial probe.
- **d35-d39**: Please confirm that coverage items should carry `university: null` rather than the out-of-corpus name.

## Multi-hop extension (2026-11-12, pending human acceptance)

18 `multi_hop` items were drafted by a model from the page text in
`data/processed/chunks.jsonl`, each with an `evidence` quote for every relevant
doc. `scripts/validate_gold.py` checks every quote against its doc (122 items
ok). A second-model review of the first 18 drafts dropped mh01 (ambiguous
embassy sentence), mh08 (early deadline left out; a second Saarland page
answers), mh12 (both hops answered equally by other pages), mh14 (one page
answers both parts), mh16 and mh17 (another page answers a hop just as well),
fixed mh02 (asks both hops), mh05 (programme metadata) and mh10 (asks facts only
its two docs state), and six replacements (mh19-mh24) were drafted with a
corpus-wide check that no other doc answers either hop. They keep
`reviewed_by: model` until the maintainer accepts them.

| qid | kind | status | docs |
|---|---|---|---|
| mh02 | multi_hop | pending | de/saarland/masters-application-guide, de/rules/embassy-india-studies-visa |
| mh03 | multi_hop | pending | de/tum/dea-msc/department, de/rules/uni-assist-faq-plan-application |
| mh04 | multi_hop | pending | de/tub/cs-msc/application, de/rules/uni-assist-apply-in-6-steps |
| mh05 | multi_hop | pending | de/scholarship/daad-study-scholarships-stem, de/kit/tuition-fees |
| mh06 | multi_hop | pending | de/rwth/ds-msc/application, de/aachen/residence-permit |
| mh07 | multi_hop | pending | de/stuttgart/residence-permit, de/rules/daad-health-insurance |
| mh09 | multi_hop | pending | de/saarland/masters-application-guide, de/tu-darmstadt/informatics-master-admission-guide |
| mh10 | multi_hop | pending | de/ustutt/tuition-fees, de/tud/semester-contribution |
| mh11 | multi_hop | pending | de/tum/language-certificates, de/kit/cs-msc/programme, de/ustutt/cs-msc/english-proofs |
| mh13 | multi_hop | pending | de/berlin/anmeldung, de/berlin/residence-permit-study |
| mh15 | multi_hop | pending | de/rules/foreign-office-blocked-account, de/darmstadt/residence-permit |
| mh18 | multi_hop | pending | de/saarland/dsai-msc/programme, de/saarbruecken/residence-permit |
| mh19 | multi_hop | pending | de/rwth/ds-msc/programme, de/saarland/dsai-msc/study-regulations |
| mh20 | multi_hop | pending | de/saarland/cs-msc/programme, de/tud/cs-msc/programme |
| mh21 | multi_hop | pending | de/tub/eecs-application-faq, de/ustutt/cs-msc/english-proofs |
| mh22 | multi_hop | pending | de/rwth/ds-msc/requirements, de/rules/embassy-india-studies-visa |
| mh23 | multi_hop | pending | de/tub/cs-msc/programme, de/rules/daad-health-insurance |
| mh24 | multi_hop | pending | de/kit/cs-msc/department, de/scholarship/deutschlandstipendium |
