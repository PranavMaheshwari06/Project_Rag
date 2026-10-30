# Completed second-pass audit

Verified: 26 October 2026. Input: `Pasted markdown(20261026-173510).md`.

**Strict field-quality score: 29/35 = 82.86%.**

| Measure | Result | Interpretation |
| --- | ---: | --- |
| Quote present in supplied excerpt | 35/35 — 100.00% | Text grounding only |
| Narrow snapshot/excerpt check | 32/35 — 91.43% | Failures: 12, 16, 28 |
| Strict full-source field check | 29/35 — 82.86% | Failures: 12, 16, 20, 22, 28, 32 |
| Fields actually audited | 35/69 — 50.72% | The other 34 fields are unscored |

The existing pre-check accepts 33/35 fields (94.29%). I would not retain that result: it overlooks the GATE-paper restriction even on the narrow check, and further loses degree-origin scope, fee precision and language-proof detail under the strict check.

## Scoring method and limits

Each row earns **1 or 0**, with equal weight and no subjective partial credit. The strict score requires correct values, relevant conditions and material list completeness. A failure does not imply every sub-item in that row is wrong.

The narrow score follows the sheet's extraction task: it permits a nominal number from an approximate quote and accepts CEFR C1 as a level shorthand. It does not require qualifiers absent from a cropped excerpt. The strict score additionally consults full official pages, the current fee page and the programme-linked language PDF. Rows 20, 22 and 32 therefore pass narrowly but fail strictly. Their treatment is stated explicitly so the denominator and rubric are reproducible.

Standard tuition amounts are scored as published tariffs for fee-liable full-time students, not as claims that no exemptions exist. `application_route: both` is assessed as availability across applicant groups, not an instruction that each person must apply twice. Degree and selection summaries are assessed for their stated scope; they do not certify complete admission eligibility.

All supplied quotes were found after removing Markdown escaping and normalizing whitespace. I manually checked the numbers, country lists and conditions, and independently revisited the relevant official sources. No repository, original extraction schema, unsampled records, or sampling script was supplied. The sheet's seed and 69-field population are reported provenance, not independently reproduced. The scores describe these 35 rows only, not population accuracy, software correctness or a verified correction run.

## All 35 row scores

In the table, **Narrow** and **Strict** are points out of one. The completed worksheet later uses the strict verdict in its auditor checkbox.

| # | Programme | Field | Narrow | Strict | Finding | Sources |
| ---: | --- | --- | ---: | ---: | --- | --- |
| 1 | KIT CDS | `english` | 1 | 1 | All eight tests and every overall/component threshold match. Non-test proof alternatives are outside this test list. | [S01](#s01) |
| 2 | KIT CDS | `language_of_instruction` | 1 | 1 | English is the published programme language; an optional German-language profile does not change that classification. | [S01](#s01) |
| 3 | KIT CDS | `min_total_ects` | 1 | 1 | 180 is the required minimum for the qualifying degree, not the master programme length. | [S01](#s01) |
| 4 | KIT CDS | `tuition_eur_per_semester_non_eu` | 1 | 1 | EUR 1,500 is the standard semester tuition for fee-liable third-country students; exemptions remain separate. | [S02](#s02) |
| 5 | Saarland CS | `application_route` | 1 | 1 | The department application system is a direct university route. | [S03](#s03), [S04](#s04) |
| 6 | Saarland CS | `aps_degree_countries` | 1 | 1 | China, India and Vietnam match; the rule concerns where the degree was obtained. | [S04](#s04) |
| 7 | Saarland CS | `deadlines` | 1 | 1 | All four early/final deadline mappings match. Early deadlines precede the target intake by the stated application cycle. | [S03](#s03) |
| 8 | Saarland CS | `degree_requirement` | 1 | 1 | Degree type, 180 CP and subject/equivalence wording match; this is not the complete eligibility rule. | [S04](#s04) |
| 9 | Saarland CS | `entrance_tests` | 1 | 1 | GRE/GATE alternative, absent minimum and degree-region exemptions match. Preserve GRE General and branch-campus restrictions. | [S04](#s04) |
| 10 | Saarland CS | `german` | 1 | 1 | No German proficiency requirement for admission is stated. | [S04](#s04) |
| 11 | Saarland CS | `language_of_instruction` | 1 | 1 | English is explicitly the teaching language. | [S04](#s04) |
| 12 | Saarland CS | `required_documents` | 0 | 0 | Listed items are supported, but mandatory English evidence and conditional GRE/GATE evidence are missing. | [S04](#s04), [S03](#s03) |
| 13 | Saarland CS | `tuition_eur_per_semester_non_eu` | 1 | 1 | No tuition is listed. The separately payable semester contribution is not tuition. | [S03](#s03) |
| 14 | TU Darmstadt AIML | `application_route` | 1 | 1 | Direct university application is correct; the guide also requires timely hard-copy documents. | [S05](#s05) |
| 15 | TU Darmstadt AIML | `degree_requirement` | 1 | 1 | The bachelor requirement of at least 180 ECTS or equivalent workload matches. | [S05](#s05) |
| 16 | TU Darmstadt AIML | `entrance_tests` | 0 | 0 | Numerical thresholds match, but unconditional one_of loses the exam trigger; condition text is misplaced in min_scores. | [S05](#s05), [S06](#s06) |
| 17 | TU Darmstadt AIML | `subject_credits` | 1 | 1 | 60 ECTS is correct; equivalence must also cover course content, level and depth. | [S05](#s05) |
| 18 | TU Dresden CS | `application_route` | 1 | 1 | both is valid across applicant groups. Correct the pre-check: German-degree and foreign-degree routes differ. | [S07](#s07) |
| 19 | TU Dresden CS | `aps_degree_countries` | 1 | 1 | China, Vietnam and India match; country-list order is immaterial. | [S08](#s08) |
| 20 | TU Dresden CS | `deadlines` | 1 | 0 | Four dates match, but EU/non-EU branches are specifically under foreign university degrees; that qualifier is missing. | [S07](#s07) |
| 21 | TU Dresden CS | `degree_requirement` | 1 | 1 | The quoted qualifying-degree requirement matches; aptitude and English are separate requirements. | [S09](#s09) |
| 22 | TU Dresden CS | `semester_fee_eur` | 1 | 0 | 360 matches an approximate FAQ estimate. The exact standard on-campus fee for winter 2026/27 is EUR 361. | [S08](#s08), [S10](#s10) |
| 23 | TUM DEA | `entrance_tests` | 1 | 1 | Five degree countries, GRE Q164/AW4.0 and annually qualifying GATE Computer Science alternative all match. | [S11](#s11) |
| 24 | TUM DEA | `language_of_instruction` | 1 | 1 | English is correct as the main language. Some individual courses can be in German. | [S11](#s11), [S12](#s12) |
| 25 | TUM DEA | `required_documents` | 1 | 1 | All 13 listed documents match, including country conditions and the explicitly optional qualification certificates. | [S11](#s11) |
| 26 | TUM DEA | `semester_fee_eur` | 1 | 1 | EUR 97 matches both the programme page and current Garching contribution page; tuition is additional. | [S12](#s12), [S15](#s15) |
| 27 | TUM Informatics | `degree_requirement` | 1 | 1 | A Computer Science/Informatics bachelor equivalent to the TUM bachelor is required. | [S13](#s13) |
| 28 | TUM Informatics | `entrance_tests` | 0 | 0 | Countries and numbers match, but the GATE alternative omits the mandatory Computer Science paper. | [S13](#s13) |
| 29 | TUM Informatics | `tuition_eur_per_semester_non_eu` | 1 | 1 | EUR 6,000 is the published full-time semester tuition; part-time proportions and waivers are separate. | [S14](#s14) |
| 30 | Stuttgart CS | `application_route` | 1 | 1 | Application via the university C@MPUS portal is a direct route. | [S17](#s17) |
| 31 | Stuttgart CS | `degree_requirement` | 1 | 1 | At least six semesters and the three subject/equivalence alternatives match. | [S16](#s16) |
| 32 | Stuttgart CS | `english` | 1 | 0 | C1 is correct, but CEFR is a framework, not a test. The linked official certificate list is omitted. | [S16](#s16), [S19](#s19) |
| 33 | Stuttgart CS | `german` | 1 | 1 | No proof of German proficiency is needed for admission. | [S16](#s16) |
| 34 | Stuttgart CS | `selection_process` | 1 | 1 | The board review, possible interview/exam and remedial-module summary matches; it does not specify a complete points model. | [S17](#s17) |
| 35 | Stuttgart CS | `tuition_eur_per_semester_non_eu` | 1 | 1 | EUR 1,500 matches the standard fee for liable non-EU/EEA international students. | [S18](#s18) |

## Programme totals

| Programme | Narrow | Strict | Strict percentage |
| --- | ---: | ---: | ---: |
| KIT CDS | 4/4 | 4/4 | 100.00% |
| Saarland CS | 8/9 | 8/9 | 88.89% |
| TU Darmstadt AIML | 3/4 | 3/4 | 75.00% |
| TU Dresden CS | 5/5 | 3/5 | 60.00% |
| TUM DEA | 4/4 | 4/4 | 100.00% |
| TUM Informatics | 2/3 | 2/3 | 66.67% |
| Stuttgart CS | 6/6 | 5/6 | 83.33% |

## Corrections required under the strict audit

### 12 — Saarland required documents

Retain the six supported items. Add English-proficiency evidence, with the guide's permitted substitute/exemption evidence, and GRE General or Indian GATE results for applicants without a qualifying degree from the stated exempt region. Preserve the ongoing-degree transcript alternative. The programme page also requires a motivation/personal statement; reconcile that with the guide before treating this as a complete application checklist. [S03](#s03), [S04](#s04).

### 16 — TU Darmstadt entrance tests

Represent the rule as conditional: invite an applicant to the entrance exam only when documents cannot establish the required competencies. Sufficient documents can establish those competencies without a test. GRE/GATE are exemption evidence, not universally mandatory alternatives. Retain GRE verbal 155, quantitative 165, writing 3.5; GATE overall 750. Retain exemption submission deadlines of August 20 (winter) and February 20 (summer). Put the trigger in a condition field, not in a score field. These are representation requirements, not a tested patch to an unseen schema. [S05](#s05), [S06](#s06).

### 20 — TU Dresden deadlines

Retain all four dates, but attach the condition that the qualifying university degree is foreign. For that population, EU deadlines are July 15 (winter) and January 15 (summer); non-EU deadlines are May 31 and November 30. German university degrees are a separate branch with aptitude registration ending July 15/January 15. Do not use nationality alone to select the branch. [S07](#s07).

### 22 — TU Dresden semester fee

For an exact current figure, replace `360.0` with `361.0`, record winter semester 2026/27, and cite the current contribution page. This covers regular on-campus studies excluding IHI and special categories. If retaining the FAQ snapshot instead, preserve that `360` is approximate; it is not an exact payment amount. The one-euro difference is a precision issue, not a major budget error. [S08](#s08), [S10](#s10).

### 28 — TUM Informatics entrance tests

Change the GATE entry to identify the Computer Science paper and require the qualifying score for that year. The source's Mechanical Engineering exception belongs to M.Sc. CSE, not Informatics. Keep the five degree countries, GRE General quantitative 164 and writing 4.0. Verbal reasoning is not assessed. Omitting the GATE paper can falsely accept a different examination, so this is substantive. [S13](#s13).

### 32 — Stuttgart English evidence

Keep CEFR C1 as a proficiency level rather than a test identity. The linked January 2026 document accepts these proof families:

| Proof | Published minimum/condition |
| --- | --- |
| TOEFL iBT | 95 on the earlier scale; 5 or better from 2026 |
| Academic IELTS | 7.0 or higher |
| Cambridge | CAE or CPE |
| Oxford Test of English Advanced | C1 |
| PTE Academic | 76 or higher |
| telc University B2/C1 | Result must be very good |
| telc general examination | C1 or C2 |

The PDF also sets certificate-validity and citizenship-plus-education exemption conditions and rejects MOI as a substitute. Encode those separately when building application eligibility logic. The narrow excerpt supports C1, but it cannot establish an accepted-test list. [S19](#s19).

## Passing rows with important interpretation notes

- **18:** Keep the aggregate `both` value only if it means different routes exist for different applicant groups. The original pre-check wrongly suggests every applicant combines uni-assist application with a separate direct assessment registration. The official page branches by degree origin. [S07](#s07).
- **9:** The region in `exempt_degree_countries` is a region label rather than an enumerated country. This is source-faithful, but downstream matching must understand it. No country-expansion or runtime behaviour was supplied for verification. [S04](#s04).
- **1:** The unusually precise PTE decimals are printed on the official KIT page. There is no evidence-based reason to round or replace them. [S01](#s01).
- **24:** The language label means the main programme language; it does not promise every module is English. [S12](#s12).
- **34:** This passes as a narrative summary. A decision engine would additionally need the admission-points rules; no numerical selection formula is certified here. [S17](#s17).

## Official source register

All sources below were checked on 26 October 2026. The Stuttgart language PDF was also visually inspected. Source-specific scope and semester labels take precedence over generic estimates.

### S01

[KIT Computational and Data Science](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php)

### S02

[KIT tuition fees](https://www.intl.kit.edu/istudies/12606.php)

### S03

[Saarland Computer Science programme](https://www.uni-saarland.de/en/study/programmes/master/informatics.html)

### S04

[Saarland application guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/)

### S05

[TU Darmstadt admissions guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp)

### S06

[TU Darmstadt entrance examination](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/entrance_exam/entrance_examination_mdss.en.jsp)

### S07

[TU Dresden aptitude assessment and application groups](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/app/infoapp/sins_eignungsfeststellung_detail?autoid=73)

### S08

[TU Dresden international FAQ](https://tu-dresden.de/studium/vor-dem-studium/internationales/faq?set_language=en)

### S09

[TU Dresden Computer Science programme](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_studiengang?autoid=73&set_language=en)

### S10

[TU Dresden current semester fee](https://tu-dresden.de/studium/im-studium/studienorganisation/rueckmeldung)

### S11

[TUM Data Engineering and Analytics department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/)

### S12

[TUM Data Engineering and Analytics programme](https://www.tum.de/en/studies/degree-programs/detail/data-engineering-and-analytics-master-of-science-msc)

### S13

[TUM Informatics department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/)

### S14

[TUM Informatics programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc)

### S15

[TUM current Munich/Garching/Freising semester contribution](https://www.tum.de/en/studies/fees-and-financial-aid/campus-munich-garching-wzw-and-tum-asia)

### S16

[Stuttgart Computer Science programme](https://www.uni-stuttgart.de/en/study/study-programs/Computer-Science-M.Sc-00002./)

### S17

[Stuttgart Computer Science department](https://www.f05.uni-stuttgart.de/en/cs/prospective-students/msc-computerscience/)

### S18

[Stuttgart fees and charges](https://www.student.uni-stuttgart.de/en/organizing-studies/formalities/tuition-and-fees/)

### S19

[Stuttgart accepted English proofs, January 2026 PDF](https://www.uni-stuttgart.de/studium/studienangebot_assets/computer-science/pdf/English_language_skills_MSc_CS_barrierefrei_01-2026.pdf)

## Completed worksheet

Original values, quotations, excerpts and pre-check comments are retained below. Pre-check comments remain historical input; the filled auditor checkbox is the strict final verdict. Corrections are recommendations in this report, not changes to an unseen dataset.

### 1. kit-m-sc-computational-and-data-science :: english



- value: `[{"test": "TOEFL iBT", "min_score": "90 points"}, {"test": "IELTS", "min_score": "overall score of at least 6.5, no section below 5.5"}, {"test": "TOEIC", "min_score": "at least 400 points in Listening, 385 in Reading, 160 in Speaking, 150 in Writing"}, {"test": "Cambridge Certificate C1 Advanced (CAE)", "min_score": "accepted certificate, no minimum score stated"}, {"test": "Cambridge Certificate C2 Proficiency (CPE)", "min_score": "accepted certificate, no minimum score stated"}, {"test": "Cambridge Certificate B2 First (FCE)", "min_score": "accepted certificate, no minimum score stated"}, {"test": "UNIcert", "min_score": "at least level II"}, {"test": "Pearson PTE Academic", "min_score": "at least 58.5 points overall and at least 56.8 in Listening, 60.6 in Reading, 53.5 in Speaking, 74.1 in Writing"}]`

- quote: "Otherwise, only the following English tests listed in the KIT admission and enrollment regulations are accepted as proof of English proficiency: - TOEFL iBT (internet-based) with at least 90 points - IELTS with an overall score of at least 6.5, no section below 5.5 - TOEIC with at least 400 points in Listening, 385 in Reading, 160 in Speaking, 150 in Writing - Cambridge Certificate C1 Advanced (CAE) - Cambridge Certificate C2 Proficiency (CPE) - Cambridge Certificate B2 First (FCE) - UNIcert, at least level II - Pearson PTE Academic with at least 58.5 points overall and at least 56.8 in Listening, 60.6 in Reading, 53.5 in Speaking, 74.1 in Writing"

- doc: `de/kit/cds-msc/programme`

- page excerpt:



  >  at least the German grade 4 (sufficient) or at least 5 grade points or - a university degree with English as the sole language of instruction and examination in the completed degree program - this must be clearly stated in the Diploma Supplement, Transcript of Records or in the degree certificate. Otherwise, only the following English tests listed in the KIT admission and enrollment regulations are accepted as proof of English proficiency: - TOEFL iBT (internet-based) with at least 90 points - IELTS with an overall score of at least 6.5, no section below 5.5 - TOEIC with at least 400 points in Listening, 385 in Reading, 160 in Speaking, 150 in Writing - Cambridge Certificate C1 Advanced (CAE) - Cambridge Certificate C2 Proficiency (CPE) - Cambridge Certificate B2 First (FCE) - UNIcert, at least level II - Pearson PTE Academic with at least 58.5 points overall and at least 56.8 in Listening, 60.6 in Reading, 53.5 in Speaking, 74.1 in Writing Note: The above-mentioned tests are accepted as proof of language proficiency for an unlimited period of time, even if the provider specifies an expiration date. #### What if I cannot provide suitable B2 proof of English at the time of application? If you are unable to provide any of the B2 certifi



- Original pre-check: agree — all eight tests and every score match the page list ("TOEFL iBT (internet-based) with at least 90 points" ... "Pearson PTE Academic with at least 58.5 points overall and at least 56.8 in Listening, 60.6 in Reading, 53.5 in Speaking, 74.1 in Writing"); the page also accepts a B2 school certificate or an English-only degree, which are not tests.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S01](#s01)

### 2. kit-m-sc-computational-and-data-science :: language_of_instruction



- value: `"English"`

- quote: "Language of instruction: English"

- doc: `de/kit/cds-msc/programme`

- page excerpt:



  > . Complementary Subject Techno-Mathematics M.Sc. Economathematics M.Sc. - Computational and Data Science M.Sc. ## Computational and Data Science Master of Science (M.Sc.) Degree: Master of Science (M.Sc.) Regular program length: 4 semester (full-time program) Credit points (ECTS): 120 credit points Language of instruction: English ### Program details #### Was dich in unserem Master erwartet Der englischsprachige Masterstudiengang Computational and Data Science am KIT ist interdisziplinär und flexibel gestaltbar ausgerichtet. Die besondere Verbindung von Data Science und Computational Science sowie die interdisziplinäre Ausri



- Original pre-check: agree — page header says "Language of instruction: English" and "Der englischsprachige Masterstudiengang"; only the optional Computational Chemistry SEE profile "wird ausschließlich in deutscher Sprache angeboten".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S01](#s01)

### 3. kit-m-sc-computational-and-data-science :: min_total_ects



- value: `180`

- quote: "Das Studium muss im Rahmen einer mindestens dreijährigen Regelstudienzeit und mit einer Mindestanzahl von 180 ECTS-Punkten absolviert worden sein."

- doc: `de/kit/cds-msc/programme`

- page excerpt:



  >  Bereichen Wirtschaftswissenschaften, Chemie, Erdsystemwissenschaften, Maschinenbau, Physik, Elektro- und Informationstechnik, Chemieingenieurwesen, Verfahrenstechnik oder Robotik an einer Universität, Fachhochschule oder Berufsakademie bzw. Dualen Hochschule oder an einer ausländischen Hochschule. Das Studium muss im Rahmen einer mindestens dreijährigen Regelstudienzeit und mit einer Mindestanzahl von 180 ECTS-Punkten absolviert worden sein. - Mindestkenntnisse und Mindestleistungen in den Bereichen Grundlagen der Mathematik (Lineare Algebra und Analysis oder Höhere Mathematik) 20 LP Mindestens 40 LP aus einem und mindestens 12 LP aus den beiden verbleibenden Gebieten: Angewandte Mathematik oder Mathematik für Computational and Data Sc



- Original pre-check: agree — page states "mit einer Mindestanzahl von 180 ECTS-Punkten absolviert worden sein" in the Zugangsvoraussetzungen.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S01](#s01)

### 4. kit-m-sc-computational-and-data-science :: tuition_eur_per_semester_non_eu



- value: `1500.0`

- quote: "According to Article 3, LHGebG (Baden-Württemberg Act on State University Fees), international students (from third countries/non-EU countries) attending bachelor’s, teacher’s, and consecutive master’s programs as well as free movers will have to pay tuition fees in the amount of EUR 1,500 per semester as from the 2017/2018 winter semester."

- doc: `de/kit/tuition-fees`

- page excerpt:



  > d to KIT Degree-Seeking Temporary Students Advice - Degree-Seeking Prior to Studies During Studies After Studies Doctoral Studies Doppelabschlussprogramme Tuition Fees, Financial Aid & Prizes - Tuition Fees, Financial Aid & Prizes Tuition Fees Financial Aid DAAD Prize - Tuition Fees ## Tuition Fees According to Article 3, LHGebG (Baden-Württemberg Act on State University Fees), international students (from third countries/non-EU countries) attending bachelor’s, teacher’s, and consecutive master’s programs as well as free movers will have to pay tuition fees in the amount of EUR 1,500 per semester as from the 2017/2018 winter semester. ## The information provided here is intended to explain the provisions of the law and the associated procedures. Please note that this text is solely for information purposes and only the in the Act on Fees in Higher Education of the Land of Baden-Württemberg (Landeshochschulgebührengesetz, LHGebG)



- Original pre-check: agree — page states "international students (from third countries/non-EU countries) attending ... consecutive master’s programs ... will have to pay tuition fees in the amount of EUR 1,500 per semester"; exemptions (Art. 5 LHGebG, refugees, disability) are individual cases.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S02](#s02)

### 5. saarland-university-m-sc-computer-science :: application_route



- value: `"direct"`

- quote: "Applications should be submitted via the online application portal managed by the Department of Computer Science where you'll find further information about application and admission procedures."

- doc: `de/saarland/cs-msc/programme`

- page excerpt:



  > e a letter of admission by mid-July if the respective Master's commission makes a positive decision. Applicants who apply by November 15th for the following winter semester are expected to receive a letter of admission by mid-February if the respective Master's commission makes a positive decision. Applications should be submitted via the online application portal managed by the Department of Computer Science where you'll find further information about application and admission procedures. - Study regulations - Examination regulations - Subject-specific regulations - Discontinued regulations - Other documents and information - Module handbook ### At a glance | Standard period of study | 4 semesters for full-time students Part-time studies are possible | | --- | --- | | Language of in



- Original pre-check: agree — page says "Applications should be submitted via the online application portal managed by the Department of Computer Science" and no Saarland page mentions uni-assist.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S03](#s03), [S04](#s04)

### 6. saarland-university-m-sc-computer-science :: aps_degree_countries



- value: `["China", "India", "Vietnam"]`

- quote: "Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate issued by the Academic Evaluation Center (Akademische Prüfstelle) in the corresponding country with the application."

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  > rmation on how to proceed. Please check them before submitting your application. We do not accept letters of recommendation sent by mail or any other means. Please note that your application is considered fully submitted only after both recommenders have filled out the review forms. APS certificate Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate issued by the Academic Evaluation Center (Akademische Prüfstelle) in the corresponding country with the application. GRE General Test / GATE test Applicants for Computer Science, Cybersecurity, DSAI, Embedded Systems and Visual Computing who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General 



- Original pre-check: agree — page says "Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S04](#s04)

### 7. saarland-university-m-sc-computer-science :: deadlines



- value: `[{"intake": "winter", "applicant_group": "all", "date": "November 15", "kind": "early"}, {"intake": "winter", "applicant_group": "all", "date": "May 15", "kind": "final"}, {"intake": "summer", "applicant_group": "all", "date": "May 15", "kind": "early"}, {"intake": "summer", "applicant_group": "all", "date": "November 15", "kind": "final"}]`

- quote: "| Application deadline for the winter semester | Early deadline: Nov 15 (positive decision: notification at the lastest in February of the following year) Late deadline: May 15 | | Application deadline for the summer semester | Early deadline: May 15 (positive decision: notification at the lastest in July) Late deadline: Nov 15 |"

- doc: `de/saarland/cs-msc/programme`

- page excerpt:



  > dbook ### At a glance | Standard period of study | 4 semesters for full-time students Part-time studies are possible | | --- | --- | | Language of instruction | English | | English language requirements | Level C1 (a MOI (Medium of Instruction) is not accepted, see FAQ ) | | Restricted entry | No | | Application deadline for the winter semester | Early deadline: Nov 15 (positive decision: notification at the lastest in February of the following year) Late deadline: May 15 | | Application deadline for the summer semester | Early deadline: May 15 (positive decision: notification at the lastest in July) Late deadline: Nov 15 | | Tuition fees | Not applicable | | Semester fee | See current fee structure | ### Contact #### Course adviser Study coordination of Computer Science Dr. in Rahel Stoike-Sy Barbara Schulz-Brünken Saarland Informatics Campus Building E1 3, Room 207-209 master(at)cs.uni-saarland.de Saarland Informati



- Original pre-check: agree — table gives winter "Early deadline: Nov 15 ... Late deadline: May 15" and summer "Early deadline: May 15 ... Late deadline: Nov 15", consistent with the application guide ("The application deadline for the winter semester ... is May 15th", "summer semester ... is November 15th").

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S03](#s03)

### 8. saarland-university-m-sc-computer-science :: degree_requirement



- value: `"Bachelor's degree from a German university (at least 180 CP) or an equivalent qualification from a foreign university in computer science, informatics or a related field"`

- quote: "Students seeking admission to the Master’s programme shall have a Bachelor’s degree from a German university (at least 180 CP) or an equivalent qualification from a foreign university in computer science, informatics or a related field:"

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  > guarantee your admission! An individual check of eligibility cannot be offered in advance to the application. ### a) Eligibility for the master‘s degree programme Please select the desired programme: - Computer Science - Data Science and Artificial Intelligence - Embedded Systems - Visual Computing Students seeking admission to the Master’s programme shall have a Bachelor’s degree from a German university (at least 180 CP) or an equivalent qualification from a foreign university in computer science, informatics or a related field: Sufficient merit in the applicant’s previous academic track record and the appropriate curricular content of the Bachelor’s degree is required. Applicants should demonstrate a level of knowledge and competence that corresponds to that acquired in the Bachelor’s degree programme in computer science 



- Original pre-check: agree — matches "shall have a Bachelor’s degree from a German university (at least 180 CP) or an equivalent qualification from a foreign university in computer science, informatics or a related field" (curricular areas and CGPA follow separately).

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S04](#s04)

### 9. saarland-university-m-sc-computer-science :: entrance_tests



- value: `[{"test": "GRE", "min_scores": null, "requirement": "one_of", "applies_to_degree_countries": [], "exempt_degree_countries": ["European Higher Education Area (EHEA) region", "Switzerland", "UK"]}, {"test": "GATE", "min_scores": null, "requirement": "one_of", "applies_to_degree_countries": [], "exempt_degree_countries": ["European Higher Education Area (EHEA) region", "Switzerland", "UK"]}]`

- quote: "Applicants for Computer Science, Cybersecurity, DSAI, Embedded Systems and Visual Computing who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General Test or the Indian GATE test ."

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  >  Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate issued by the Academic Evaluation Center (Akademische Prüfstelle) in the corresponding country with the application. GRE General Test / GATE test Applicants for Computer Science, Cybersecurity, DSAI, Embedded Systems and Visual Computing who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General Test or the Indian GATE test . There is no minimum score requirement and we accept home editions of the GRE/GATE tests . There are no exceptions from this requirement for degrees from branch campuses located in non-EHEA countries. The GRE test result of one of the subject tests or a prep test does not satisfy this requirement. A



- Original pre-check: agree — "who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General Test or the Indian GATE test" and "There is no minimum score requirement", so one_of with null scores and those three exemptions is right.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S04](#s04)

### 10. saarland-university-m-sc-computer-science :: german



- value: `{"min_level": "none", "needed_by": "admission"}`

- quote: "Knowledge of proficiency in German is not required."

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  > onstrating that English has been studied for at least 5 years up to the general qualification for university entrance (Abitur) with good or very good grades is sufficient. As level C1 is not usually achieved by the end of school, certificates with good or very good grades are examined individually. Knowledge of proficiency in German is not required. ### c) Recommendations by academic members in the subject Two complete review forms filled out by recommenders appointed by the applicant in the application system. These recommenders can optionally upload an additional recommendation letter. At least one recommender should know the applicant acade



- Original pre-check: agree — guide says "Knowledge of proficiency in German is not required."

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S04](#s04)

### 11. saarland-university-m-sc-computer-science :: language_of_instruction



- value: `"English"`

- quote: "The teaching language of the master’s degree programme is English."

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  > puting (e.g. machine learning, data science, artificial intelligence, telecommunication, robotics) Minimal prerequisite is a cumulative undergraduate grade point average (CGPA) of 75% or 3.00 GPA on a 4 point scale and ranking in the top 10% of the graduating class. ### b) Necessary language skills The teaching language of the master’s degree programme is English. All applicants from all countries must provide a proof of advanced proficiency in English (level C1 of the Common European Framework). The following certificates will be accepted: _ IELTS (academic test): min. 7.0 out of 9 _ TOEFL (internet based): min. 95 out of 120 (2026: 5 out of 6) _ TOEFL (pap



- Original pre-check: agree — guide says "The teaching language of the master’s degree programme is English." and the programme table says "Language of instruction | English".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S04](#s04)

### 12. saarland-university-m-sc-computer-science :: required_documents



- value: `["copy of university entrance qualification", "copies of 3 most recent degrees (with certified translation, if the original language is not English, German or French)", "certified list of all attended courses with the respective grades, including an explanation of the grading system", "Curriculum Vitae (CV)", "two complete review forms by recommenders appointed by the applicant", "APS certificate (if degree obtained in China, India or Vietnam)"]`

- quote: "Transcripts (Academic Records): _ a copy of your university entrance qualification _ copies of your 3 most recent degrees\* (with certified translation, if the original language is not English, German or French) _ a certified list of all attended courses with the respective grades, including an explanation of the grading system \*If your current degree is ongoing, please include a recent transcript showing your current progress. Minimal prerequisite is a cumulative undergraduate grade point average of 75% and ranking in the top 10% of the graduating class. Curriculum Vitae (CV) including information on your areas of interest in research, as well as any projects or publications Letters of Recommendation A complete application includes two complete review forms by recommenders appointed by the applicant. These recommenders can optionally upload an additional recommendation letter. It is your responsibility to ensure that your referees have the information they need to provide a reference and submit it by the deadline. It is extremely important to enter valid email addresses of your referees! An email will be sent to your recommenders with information on how to proceed. Please check them before submitting your application. We do not accept letters of recommendation sent by mail or any other means. Please note that your application is considered fully submitted only after both recommenders have filled out the review forms. APS certificate Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate issued by the Academic Evaluation Center (Akademische Prüfstelle) in the corresponding country with the application."

- doc: `de/saarland/masters-application-guide`

- page excerpt:



  >  need to submit the following documents with your application in order to be considered for admission. Please note that we only accept files in the PDF file format. Please check all documents you upload carefully, as you will not be able to upload revised versions after submitting your application. Transcripts (Academic Records): _ a copy of your university entrance qualification _ copies of your 3 most recent degrees\* (with certified translation, if the original language is not English, German or French) _ a certified list of all attended courses with the respective grades, including an explanation of the grading system \*If your current degree is ongoing, please include a recent transcript showing your current progress. Minimal prerequisite is a cumulative undergraduate grade point average of 75% and ranking in the top 10% of the graduating class. Curriculum Vitae (CV) including information on your areas of interest in research, as well as any projects or publications Letters of Recommendation A complete application includes two complete review forms by recommenders appointed by the applicant. These recommenders can optionally upload an additional recommendation letter. It is your responsibility to ensure that your referees have the information they need to provide a reference and submit it by the deadline. It is extremely important to enter valid email addresses of your referees! An email will be sent to your recommenders with information on how to proceed. Please check them before submitting your application. We do not accept letters of recommendation sent by mail or any other means. Please note that your application is considered fully submitted only after both recommenders have filled out the review forms. APS certificate Applicants who have obtained their university degree in China, India or Vietnam are required to submit the original ( digitally signed ) APS Certificate issued by the Academic Evaluation Center (Akademische Prüfstelle) in the corresponding country with the application. GRE General Test / GATE test Applicants for Computer Science, Cybersecurity, DSAI, Embedded Systems and Visual Computing who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General 



- Original pre-check: disagree — the six items match the quote, but the same "Required Application Documents" section also requires the GRE/GATE result ("Applicants ... who have no degree certificate earned within the European Higher Education Area (EHEA) region, Switzerland, or the UK are required to upload the test result from the GRE General Test or the Indian GATE test") and the English certificate ("The English certificate is a mandatory part of the application"), so the list is incomplete.

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 0/1; strict 0/1.
- Verified source(s): [S04](#s04), [S03](#s03)

### 13. saarland-university-m-sc-computer-science :: tuition_eur_per_semester_non_eu



- value: `0.0`

- quote: "| Tuition fees | Not applicable |"

- doc: `de/saarland/cs-msc/programme`

- page excerpt:



  > inter semester | Early deadline: Nov 15 (positive decision: notification at the lastest in February of the following year) Late deadline: May 15 | | Application deadline for the summer semester | Early deadline: May 15 (positive decision: notification at the lastest in July) Late deadline: Nov 15 | | Tuition fees | Not applicable | | Semester fee | See current fee structure | ### Contact #### Course adviser Study coordination of Computer Science Dr. in Rahel Stoike-Sy Barbara Schulz-Brünken Saarland Informatics Campus Building E1 3, Room 207-209 master(at)cs.uni-saarland.de Saarland Informatics Campus #### Central Student Adv



- Original pre-check: agree — programme table says "Tuition fees | Not applicable"; no Saarland page states a non-EU fee.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S03](#s03)

### 14. tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning :: application_route



- value: `"direct"`

- quote: "Apply via the Online Application Portal ."

- doc: `de/tu-darmstadt/informatics-master-admission-guide`

- page excerpt:



  >  your courses equivalent in content, academic level, and depth to our core subjects meet or exceed 60 ECTS , proceed to Step 1 – submit your online application. We do not offer individual pre-assessments of eligibility; please do not send module descriptions. Step 1 – Submit your online application Apply via the Online Application Portal . - Application period: June 1 st – July 15 th for the winter semester December 1 st – January 15 th for the summer semester - Application portal FAQ Outside the application period, the Online Application Portal does not list our programs as available options. Step 2 – Send certified hard‑copy docume



- Original pre-check: agree — "Step 1 – Submit your online application Apply via the Online Application Portal" (TU Darmstadt's TUCaN portal plus hard copies by post); no uni-assist route is mentioned.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S05](#s05)

### 15. tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning :: degree_requirement



- value: `"Bachelor’s degree comprising at least 180 ECTS (or an equivalent workload)"`

- quote: "- Bachelor’s degree comprising at least 180 ECTS (or an equivalent workload)"

- doc: `de/tu-darmstadt/informatics-master-admission-guide`

- page excerpt:



  >  (Module Handbook, Study and Examination Plan, Regulations) | ### Important! You may apply for only one of the English-taught Master’s programs listed above in any admission period (other TU Darmstadt programs are unaffected). ### Admission Criteria Academic eligibility (content‑related evaluation) - Bachelor’s degree comprising at least 180 ECTS (or an equivalent workload) - Minimum 60 ECTS must match the core courses of our B.Sc. Informatik in content, academic level, and depth - Grades / GPA: Are not used in admission decisions; only course content is assessed - Professional experience: Admission decisions are based exclusively on academic coursework English langua



- Original pre-check: agree — page lists "Bachelor’s degree comprising at least 180 ECTS (or an equivalent workload)" under Admission Criteria; the 60 ECTS core-course match is a separate field.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S05](#s05)

### 16. tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning :: entrance_tests



- value: `[{"test": "Entrance Exam", "min_scores": "Only when required entrance competencies cannot be confirmed from the submitted documents; GRE or GATE scores below exempt", "requirement": "one_of", "applies_to_degree_countries": [], "exempt_degree_countries": []}, {"test": "GRE", "min_scores": "Verbal Reasoning ≥ 155 Quantitative Reasoning ≥ 165 Analytical Writing ≥ 3.5", "requirement": "one_of", "applies_to_degree_countries": [], "exempt_degree_countries": []}, {"test": "GATE", "min_scores": "Overall ≥ 750", "requirement": "one_of", "applies_to_degree_countries": [], "exempt_degree_countries": []}]`

- quote: "| Required for: | Only applicants to our English-taught Master’s programs Only when required entrance competencies cannot be confirmed from the submitted documents | | Format: | On-site at TU Darmstadt using pre-configured university computers (personal devices not permitted) Access to the digital exam is only possible via the university network | | When: | Typically first week of September (for winter semester) Typically first week of March (for summer semester) | | Duration: | 90 minutes | | Language: | English | | Scope: | Same exam for all English-taught Master’s programs Sample questions on Entrance Exam website | | Exemption from the Entrance Exam: Provide one of the following no later than August 20 th (for winter semester) or February 20 th (for summer semester). We strongly recommend submitting your scores as early as possible. | | Test | Required scores | How to submit | | GRE | Verbal Reasoning ≥ 155 Quantitative Reasoning ≥ 165 Analytical Writing ≥ 3.5 | Via ETS Institution Code 2249 Department Code 0402 (Computer Science) GRE Home accepted only if submitted through ETS | | GATE | Overall ≥ 750 | Send via e-mail to application@informatik… |"

- doc: `de/tu-darmstadt/informatics-master-admission-guide`

- page excerpt:



  > te applications can be reviewed sooner. If admitted, early applicants receive their admission decision sooner, which supports timely visa appointments, housing, and course enrolment. ### Entrance Exam – Key Facts | For full information and preparation tips, visit the Entrance Exam website | | --- | | Required for: | Only applicants to our English-taught Master’s programs Only when required entrance competencies cannot be confirmed from the submitted documents | | Format: | On-site at TU Darmstadt using pre-configured university computers (personal devices not permitted) Access to the digital exam is only possible via the university network | | When: | Typically first week of September (for winter semester) Typically first week of March (for summer semester) | | Duration: | 90 minutes | | Language: | English | | Scope: | Same exam for all English-taught Master’s programs Sample questions on Entrance Exam website | | Exemption from the Entrance Exam: Provide one of the following no later than August 20 th (for winter semester) or February 20 th (for summer semester). We strongly recommend submitting your scores as early as possible. | | Test | Required scores | How to submit | | GRE | Verbal Reasoning ≥ 155 Quantitative Reasoning ≥ 165 Analytical Writing ≥ 3.5 | Via ETS Institution Code 2249 Department Code 0402 (Computer Science) GRE Home accepted only if submitted through ETS | | GATE | Overall ≥ 750 | Send via e-mail to application@informatik… | | The required minimum scores are binding – there are no exceptions. Missing points in one category cannot be compensated by higher scores in another. Results from different tests cannot be combined. | | No individual confirmation is sent upon receipt of GRE or GATE scores. GRE/GATE results are rev



- Original pre-check: disagree — scores are right ("Verbal Reasoning ≥ 155 Quantitative Reasoning ≥ 165 Analytical Writing ≥ 3.5", "GATE | Overall ≥ 750") but the scope is wrong: requirement "one_of" makes a test mandatory for everyone, while the page says the Entrance Exam is "Only when required entrance competencies cannot be confirmed from the submitted documents" and GRE/GATE are an "Exemption from the Entrance Exam" ("Submission of valid GRE or GATE scores ... may qualify applicants for exemption"); an applicant whose documents suffice needs none of them.

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 0/1; strict 0/1.
- Verified source(s): [S05](#s05), [S06](#s06)

### 17. tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning :: subject_credits



- value: `[{"area": "core courses of our B.Sc. Informatik", "min_ects": 60}]`

- quote: "- Minimum 60 ECTS must match the core courses of our B.Sc. Informatik in content, academic level, and depth"

- doc: `de/tu-darmstadt/informatics-master-admission-guide`

- page excerpt:



  > You may apply for only one of the English-taught Master’s programs listed above in any admission period (other TU Darmstadt programs are unaffected). ### Admission Criteria Academic eligibility (content‑related evaluation) - Bachelor’s degree comprising at least 180 ECTS (or an equivalent workload) - Minimum 60 ECTS must match the core courses of our B.Sc. Informatik in content, academic level, and depth - Grades / GPA: Are not used in admission decisions; only course content is assessed - Professional experience: Admission decisions are based exclusively on academic coursework English language proficiency - IELTS overall ≥ 7.0 or TOEFL iBT ≥ 95 - Or an official confirmation that English was the la



- Original pre-check: agree — page says "Minimum 60 ECTS must match the core courses of our B.Sc. Informatik in content, academic level, and depth".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S05](#s05)

### 18. tu-dresden-m-sc-computer-science :: application_route



- value: `"both"`

- quote: "Please note: If you are required to apply via the uni-assist portal, you will receive all information regarding the application and the aptitude assessment process from uni-assist."

- doc: `de/tud/cs-msc/aptitude-assessment`

- page excerpt:



  > the Common European Framework of Reference for Languages are required. Proof is provided by means of a relevant certificate or language certificate webpage of the faculty ## Registration for the aptitude assessment or the NC selection process as well as application for admission to a degree program Please note: If you are required to apply via the uni-assist portal, you will receive all information regarding the application and the aptitude assessment process from uni-assist. Registration for the aptitude assessment or selection procedure Your degree program requires participation in an aptitude assessment or selection procedure conducted by your future faculty. You must have the documents listed in the next section ready for this purpose. Please pay attention to the in



- Original pre-check: agree — the programme application goes through uni-assist ("Application address: The application takes place online via uni-assist e.V.") while the aptitude assessment is registered directly ("must beu performed online via the aptidude assesssment portal"), so "both" fits.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S07](#s07)

### 19. tu-dresden-m-sc-computer-science :: aps_degree_countries



- value: `["China", "Vietnam", "India"]`

- quote: "Applicants with Chinese, Vietnamese or Indian educational certificates must submit a certificate from the Academic Evaluation Center (APS) with their application."

- doc: `de/tud/international-faq`

- page excerpt:



  > However, you have the opportunity to check the evaluation of your certificates yourself. Uni-assist and TU Dresden follow the recommendations of the ZAB (Central Office for Foreign Education in Germany) when checking certificates. These recommendations are publicly available in the Anabin database. Applicants with Chinese, Vietnamese or Indian educational certificates must submit a certificate from the Academic Evaluation Center (APS) with their application. The responsible testing center will carry out a document check. Under certain circumstances, this may also include a plausibility interview. They then issues a certificate (APS certificate), which is required by German universities as an admission requirement. This certificate certifies that the do



- Original pre-check: agree — FAQ says "Applicants with Chinese, Vietnamese or Indian educational certificates must submit a certificate from the Academic Evaluation Center (APS)".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S08](#s08)

### 20. tu-dresden-m-sc-computer-science :: deadlines



- value: `[{"intake": "winter", "applicant_group": "non_eu", "date": "31st May", "kind": "final"}, {"intake": "summer", "applicant_group": "non_eu", "date": "30th November", "kind": "final"}, {"intake": "winter", "applicant_group": "eu", "date": "15th July", "kind": "final"}, {"intake": "summer", "applicant_group": "eu", "date": "15th January", "kind": "final"}]`

- quote: "- Application period: EU applicants: 1st April – 15th July , 1st October – 15th January Non-EU applicants: 1st April – 31st May , 1st October – 30th November"

- doc: `de/tud/cs-msc/aptitude-assessment`

- page excerpt:



  > gistration period for aptitude assessment procedures for postgraduates: 1st June – 15th July , 1st December – 15th January - Application address: The registration for the aptitude assessment must beu performed online via the aptidude assesssment portal , where the relevant documents must be upload. - Application period: EU applicants: 1st April – 15th July , 1st October – 15th January Non-EU applicants: 1st April – 31st May , 1st October – 30th November - Application address: The application takes place online via uni-assist e.V. As part of the application process with uni-assist, you will receive further information about the aptitude assessment procedure. ### Further links and information - Additional information: Notes and Rules of Procedure fo



- Original pre-check: agree — page gives "EU applicants: 1st April – 15th July , 1st October – 15th January Non-EU applicants: 1st April – 31st May , 1st October – 30th November" (same on the programme page); the separate aptitude-assessment registration deadlines ("1st June – 15th July , 1st December – 15th January") are not earlier than these.

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 1/1; strict 0/1.
- Verified source(s): [S07](#s07)

### 21. tu-dresden-m-sc-computer-science :: degree_requirement



- value: `"A first professionally qualifying university degree recognized in Germany or a degree from a state or state-recognized vocational academy in computer science."`

- quote: "The prerequisite for admission to the course is a first professionally qualifying university degree recognized in Germany or a degree from a state or state-recognized vocational academy in computer science."

- doc: `de/tud/cs-msc/programme`

- page excerpt:



  > ester): 1st October – 15th January ## Table of contents - Admission requirements - Notes on the application process - General information about the degree program - Study contents - Particularities - Occupational fields - Study documents - Contacts - Additional information ## Admission requirements The prerequisite for admission to the course is a first professionally qualifying university degree recognized in Germany or a degree from a state or state-recognized vocational academy in computer science. In addition, a special aptitude is required. Proof of special aptitude is provided through aptitude assessment procedures in accordance with the Master Computer Science aptitude assessment regulations. In addition, English language skills at level C 1 of the Common European Framework of Reference f



- Original pre-check: agree — verbatim from "The prerequisite for admission to the course is a first professionally qualifying university degree recognized in Germany or a degree from a state or state-recognized vocational academy in computer science."

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S09](#s09)

### 22. tu-dresden-m-sc-computer-science :: semester_fee_eur



- value: `360.0`

- quote: "The semester contribution costs approx. 360 € for direct study students."

- doc: `de/tud/international-faq`

- page excerpt:



  > tudent body . The fee usually also includes the semester ticket for local public transport in Germany. The semester contribution is not a tuition fee and must also be paid by students who are studying at TU Dresden as part of an exchange program (e.g. Erasmus) or as part of a double degree program. The semester contribution costs approx. 360 € for direct study students. Different rules apply for distance learning students, so called "Nebenhörer" and students on leave of absence. You will be informed about the exact amount to be transferred and the payment modalities during the enrollment process. As a rule, the university must have a valid health insurance status 



- Original pre-check: agree — FAQ says "The semester contribution costs approx. 360 € for direct study students" (an approximate figure; exact amount given at enrolment).

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 1/1; strict 0/1.
- Verified source(s): [S08](#s08), [S10](#s10)

### 23. tum-m-sc-data-engineering-and-analytics :: entrance_tests



- value: `[{"test": "GRE", "min_scores": "Quantitative reasoning: 164; Analytical writing: 4.0 (verbal reasoning not taken into account)", "requirement": "one_of", "applies_to_degree_countries": ["Bangladesh", "China", "India", "Iran", "Pakistan"], "exempt_degree_countries": []}, {"test": "GATE", "min_scores": "minimal qualifying score of the respective year (Computer Science test)", "requirement": "one_of", "applies_to_degree_countries": ["Bangladesh", "China", "India", "Iran", "Pakistan"], "exempt_degree_countries": []}]`

- quote: "Applicants with a Degree from Bangladesh, China, India, Iran or Pakistan have to submit a GRE (General) Test. We have defined required minimum scores, lower scores will not be accepted! The required scores are: Verbal reasoning: (will not be taken into account anymore) Quantitative reasoning: 164 Analytical writing: 4.0 The Institution Code: 7806, Department: 5199 ("all other departments"). Alternatively, students can submit a scorecard of the Indian GATE test (Computer Science; for M.Sc. CSE the Mechanical Engineering Test will also be accepted). The minimal qualifying score of the respective year is necessary."

- doc: `de/tum/dea-msc/department`

- page excerpt:



  > n Center (APS) You don't have to submit an entire application for a specific program to uni-assist, you only have to apply for the general preliminary documentation (VPD). An application for a VPD via uni-assist alone does not qualify as an application for a degree program at TUM. #### GRE and GATE Applicants with a Degree from Bangladesh, China, India, Iran or Pakistan have to submit a GRE (General) Test. We have defined required minimum scores, lower scores will not be accepted! The required scores are: Verbal reasoning: (will not be taken into account anymore) Quantitative reasoning: 164 Analytical writing: 4.0 The Institution Code: 7806, Department: 5199 ("all other departments"). Alternatively, students can submit a scorecard of the Indian GATE test (Computer Science; for M.Sc. CSE the Mechanical Engineering Test will also be accepted). The minimal qualifying score of the respective year is necessary. #### Certificate from the German Evaluation Center (Akademischen Prüfstelle, APS) Applicants with an undergraduate degree from China, India and Vietnam have to submit a certificate from the German Evaluation Center (APS). ### Qualification Requirements and Assessment Process Students with a Bachelo



- Original pre-check: agree — "Applicants with a Degree from Bangladesh, China, India, Iran or Pakistan have to submit a GRE (General) Test" with "Quantitative reasoning: 164 Analytical writing: 4.0", verbal "will not be taken into account", and "Alternatively ... the Indian GATE test (Computer Science ...) The minimal qualifying score of the respective year".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S11](#s11)

### 24. tum-m-sc-data-engineering-and-analytics :: language_of_instruction



- value: `"English"`

- quote: "Language of Instruction : English"

- doc: `de/tum/dea-msc/department`

- page excerpt:



  > **# Data Engineering and Analytics ## Master of Science (M.Sc.) Before Studying | During your Studies | Contact ### Key Data Type of Study : Full-time Standard Duration of Studies : 4 semesters Credits: 120 ECTS Main Locations : Garching Start of Degree Program : Summer or Winter semester Language of Instruction : English Costs: Semester fees , tuitions fees for Students from Non-EU Countries Professional Profile: Data Science and Artificial Intelligence ## Application and Admission The M.Sc. Data Engineering and Analytics welcomes students with a Bachelor's degree in Informatics who want to specialize in the area o**



- Original pre-check: agree — department page says "Language of Instruction : English"; note the programme page qualifies it: "usually English ... Some courses may, however, be taught in German."

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S11](#s11), [S12](#s12)

### 25. tum-m-sc-data-engineering-and-analytics :: required_documents



- value: `["A statement of reasons explaining why you have chosen this master’s program and TUM specifically (max. 2 pages)", "Your CV/résumé", "A scientific essay of approx. 1,000 words on a specified topic", "Form \\"Analysis of the Curriculum\\"", "Bachelor's degree certificate, including a list of courses and grades, OR an official transcript of records (documents not issued in German or English must be translated and notarized by a sworn translator)", "Curriculum (module descriptions, course catalog or syllabus) of the underlying university degree", "Proof of your English language proficiency", "GRE or Gate score for applicants with a B.Sc. degree from Bangladesh, China, India, Iran, Pakistan", "Preliminary documentation from uni-assist for all applicants with a Bachelor's degree from outside Germany", "APS certificate for applicants with a Bachelor's from China, Vietnam or India", "Certificates from professional training or additional qualifications related to the program (not mandatory)", "A passport photo", "A copy of your passport"]`

- quote: "- A statement of reasons explaining why you have chosen this master’s program and TUM specifically (max. 2 pages) - Your CV/résumé - A scientific essay of approx. 1,000 words on a specified topic (see below) - Form " Analysis of the Curriculum " (see below) - Bachelor's degree certificate, including a list of courses and grades OR an official transcript of records. Documents not issued in German or English must be translated and notarized by a sworn translator . - Curriculum (module descriptions, course catalog or syllabus) of the underlying university degree; this document is very important for the check of the academic qualification! - Proof of your English language proficiency - GRE or Gate score for applicants with a B.Sc. degree from Bangladesh, China, India, Iran, Pakistan (original scorecard or have the score transmitted directly via ETS) - Preliminary documentation from uni-assist for all applicants with a Bachelor's degree from outside Germany - APS certificate for applicants with a Bachelor's from China, Vietnam or India - Certificates from professional training or additional qualifications related to the program (e.g. participation in research competitions, internships, etc.) (not mandatory) - A passport photo - A copy of your passport"

- doc: `de/tum/dea-msc/department`

- page excerpt:



  >  additional documents as certified copies for the enrollment. Application for a Master's program - step by step ### Which Documents do I need to submit with my Application? The following documents have to be submitted for the application (the required documents may vary depending on the applicant): - A statement of reasons explaining why you have chosen this master’s program and TUM specifically (max. 2 pages) - Your CV/résumé - A scientific essay of approx. 1,000 words on a specified topic (see below) - Form " Analysis of the Curriculum " (see below) - Bachelor's degree certificate, including a list of courses and grades OR an official transcript of records. Documents not issued in German or English must be translated and notarized by a sworn translator . - Curriculum (module descriptions, course catalog or syllabus) of the underlying university degree; this document is very important for the check of the academic qualification! - Proof of your English language proficiency - GRE or Gate score for applicants with a B.Sc. degree from Bangladesh, China, India, Iran, Pakistan (original scorecard or have the score transmitted directly via ETS) - Preliminary documentation from uni-assist for all applicants with a Bachelor's degree from outside Germany - APS certificate for applicants with a Bachelor's from China, Vietnam or India - Certificates from professional training or additional qualifications related to the program (e.g. participation in research competitions, internships, etc.) (not mandatory) - A passport photo - A copy of your passport International applicants: Attention: If you did not obtain your Bachelor's degree in Germany, you have to upload a preliminary documentation from uni-assist (VPD) . More information on Preliminary Documentation (VPD) by uni-assist . Please do check the requirements for Notarization , especially for



- Original pre-check: agree — all 13 items match the page list in order, from "A statement of reasons ... (max. 2 pages)" to "A copy of your passport", with the professional certificates correctly marked "(not mandatory)".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S11](#s11)

### 26. tum-m-sc-data-engineering-and-analytics :: semester_fee_eur



- value: `97.0`

- quote: "- Student Fees: 97.00 €"

- doc: `de/tum/dea-msc/programme`

- page excerpt:



  > arge amounts of data using innovative computer science techniques. Course Homepage ## Key Data - Full-time - 4 semesters (fulltime) - 120 ECTS - Garching Winter semester: 01.02. – 31.05. Summer semester: 01.10. – 30.11. - Aptitude Assessment for Master - Possible for both winter and summer semester - Student Fees: 97.00 € - Tuition fees for international students - English ## Information on Degree Program ### Program profile Handling and analyzing very large amounts of data is an urgent problem in many areas of science and industry and requires novel approaches and techniques. The trend towards “Big Data” is caused 



- Original pre-check: agree — Key Data says "Student Fees: 97.00 €" (Garching); the page notes the semester fee "varies depending on where you are studying".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S12](#s12), [S15](#s15)

### 27. tum-m-sc-informatics :: degree_requirement



- value: `"Bachelor’s degree in Informatics / Computer Science which is equivalent to the B.Sc. Informatics taught at TUM"`

- quote: "Students with a Bachelor’s degree in Informatics / Computer Science which is equivalent to the B.Sc. Informatics taught at TUM are eligible to apply."

- doc: `de/tum/informatics-msc/department`

- page excerpt:



  > tive year is necessary. #### Certificate from the German Evaluation Center (Akademischen Prüfstelle, APS) Applicants with an undergraduate degree from China, India and Vietnam have to submit a certificate from the German Evaluation Center (APS). ### Qualification Requirements and Assessment Process Students with a Bachelor’s degree in Informatics / Computer Science which is equivalent to the B.Sc. Informatics taught at TUM are eligible to apply. Other programs do not qualify for this Master's degree. Applicants also have to provide a proof of sufficient English language proficiency . Overview assessment process valid from 01 Sep, 2024: ### Analysis of the Curriculum Before filling the form for the analysis of curriculum, you have to do and



- Original pre-check: agree — page says "Students with a Bachelor’s degree in Informatics / Computer Science which is equivalent to the B.Sc. Informatics taught at TUM are eligible to apply. Other programs do not qualify".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S13](#s13)

### 28. tum-m-sc-informatics :: entrance_tests



- value: `[{"test": "GRE", "min_scores": "Quantitative reasoning: 164 Analytical writing: 4.0", "requirement": "one_of", "applies_to_degree_countries": ["Bangladesh", "China", "India", "Iran", "Pakistan"], "exempt_degree_countries": []}, {"test": "GATE", "min_scores": "minimal qualifying score of the respective year", "requirement": "one_of", "applies_to_degree_countries": ["Bangladesh", "China", "India", "Iran", "Pakistan"], "exempt_degree_countries": []}]`

- quote: "Applicants with a Degree from Bangladesh, China, India, Iran or Pakistan have to submit a GRE (General) Test. We have defined required minimum scores, lower scores will not be accepted! The required scores are: Verbal reasoning: (will not be taken into account anymore) Quantitative reasoning: 164 Analytical writing: 4.0 The Institution Code: 7806, Department: 5199 ("all other departments"). Alternatively, students can submit a scorecard of the Indian GATE test (Computer Science; for M.Sc. CSE the Mechanical Engineering Test will also be accepted). The minimal qualifying score of the respective year is necessary."

- doc: `de/tum/informatics-msc/department`

- page excerpt:



  > n Center (APS) You don't have to submit an entire application for a specific program to uni-assist, you only have to apply for the general preliminary documentation (VPD). An application for a VPD via uni-assist alone does not qualify as an application for a degree program at TUM. #### GRE and GATE Applicants with a Degree from Bangladesh, China, India, Iran or Pakistan have to submit a GRE (General) Test. We have defined required minimum scores, lower scores will not be accepted! The required scores are: Verbal reasoning: (will not be taken into account anymore) Quantitative reasoning: 164 Analytical writing: 4.0 The Institution Code: 7806, Department: 5199 ("all other departments"). Alternatively, students can submit a scorecard of the Indian GATE test (Computer Science; for M.Sc. CSE the Mechanical Engineering Test will also be accepted). The minimal qualifying score of the respective year is necessary. #### Certificate from the German Evaluation Center (Akademischen Prüfstelle, APS) Applicants with an undergraduate degree from China, India and Vietnam have to submit a certificate from the German Evaluation Center (APS). ### Qualification Requirements and Assessment Process Students with a Bachelo



- Original pre-check: agree — "Bangladesh, China, India, Iran or Pakistan", "Quantitative reasoning: 164 Analytical writing: 4.0" and GATE "minimal qualifying score of the respective year" all match; the value omits that the GATE must be the "(Computer Science ...)" paper, a minor detail.

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 0/1; strict 0/1.
- Verified source(s): [S13](#s13)

### 29. tum-m-sc-informatics :: tuition_eur_per_semester_non_eu



- value: `6000.0`

- quote: "The tuition fees for international students from third countries for this degree program are 6,000 euros per semester ."

- doc: `de/tum/informatics-msc/programme`

- page excerpt:



  >  at the services of our Language Center. Languages of instruction: The language of instruction for this program is usually English. ### Information on study organization - Contact BAföG Confirmations Prof. Harald Räcke - Information on exams - Information on studying abroad ### Fees for the program The tuition fees for international students from third countries for this degree program are 6,000 euros per semester . This amount is charged for full-time study. Tuition fees are charged proportionately for part-time study. Many international students can have their fees waived or receive scholarships to finance them. You can find all information on waivers and scholarships here. Please note: The semester fee as a



- Original pre-check: agree — programme page says "The tuition fees for international students from third countries for this degree program are 6,000 euros per semester" (full-time; proportional for part-time).

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S14](#s14)

### 30. university-of-stuttgart-m-sc-computer-science :: application_route



- value: `"direct"`

- quote: "The application has to be done vis the online portal C@mpus ."

- doc: `de/ustutt/cs-msc/department`

- page excerpt:



  > ee to better assess your Bachelor's degree and award admission points accordingly. Please follow this link . It will take you directly to the online form. At the end of the completion process, you will receive a PDF, which you upload to the C@mpus portal in the "Supplementary form" section, please. The application has to be done vis the online portal C@mpus . The portal will open approximately one and a half months previous to the application deadline. Please notice that all documents have to be uploaded. No written applications are accepted anymore. ### Deadlines Admission to the MSc Computer Science is possible for the winter semester and for the summ



- Original pre-check: agree — department page says "The application has to be done vis the online portal C@mpus" and "No written applications are accepted anymore"; no uni-assist route is mentioned.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S17](#s17)

### 31. university-of-stuttgart-m-sc-computer-science :: degree_requirement



- value: `"bachelor's degree (or equivalent) with a duration of at least 6 semesters in Computer Science, Software Engineering or in a subject closely related"`

- quote: "General requirement is a bachelor's degree (or equivalent) with a duration of at least 6 semesters in Computer Science, Software Engineering or in a subject closely related."

- doc: `de/ustutt/cs-msc/programme`

- page excerpt:



  > fice that are offered on a regular basis. We look forward to your registration! - Studying abroad information sessions, partner universities, language requirements, application deadlines, scholarships ### Application and admission: how do I get a place at the University? #### Admission Requirements General requirement is a bachelor's degree (or equivalent) with a duration of at least 6 semesters in Computer Science, Software Engineering or in a subject closely related. The complete information on the admission process, required knowledge of English, and the criteria for the assessment of professional suitability can be found in the admission regulations. - General information on the Master's application #### Language Requirements For an admission, you need to pro



- Original pre-check: agree — page says "a bachelor's degree (or equivalent) with a duration of at least 6 semesters in Computer Science, Software Engineering or in a subject closely related", matching the department page.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S16](#s16)

### 32. university-of-stuttgart-m-sc-computer-science :: english



- value: `[{"test": "CEFR", "min_score": "C1"}]`

- quote: "For an admission, you need to prove sufficient knowledge of the English language on CEFR level C1 (Common European Framework of Reference for Languages)."

- doc: `de/ustutt/cs-msc/programme`

- page excerpt:



  >  or in a subject closely related. The complete information on the admission process, required knowledge of English, and the criteria for the assessment of professional suitability can be found in the admission regulations. - General information on the Master's application #### Language Requirements For an admission, you need to prove sufficient knowledge of the English language on CEFR level C1 (Common European Framework of Reference for Languages). Please note that you don't need a proof for German language proficiency (since the program is taught in English). Please find more details in this document: - English Language Skills M. Sc. Computer Science Please apply for this study program 9 months in advance. All applications will be evaluated 



- Original pre-check: agree — page says "prove sufficient knowledge of the English language on CEFR level C1"; the department page gives only examples ("recognized certificates e.g. TOEFL iBT score 95 or IELTS Band 7").

- auditor: [ ] agree  [x] disagree
- Scores: quote 1/1; narrow 1/1; strict 0/1.
- Verified source(s): [S16](#s16), [S19](#s19)

### 33. university-of-stuttgart-m-sc-computer-science :: german



- value: `{"min_level": "none", "needed_by": "admission"}`

- quote: "Please note that you don't need a proof for German language proficiency (since the program is taught in English)."

- doc: `de/ustutt/cs-msc/programme`

- page excerpt:



  >  professional suitability can be found in the admission regulations. - General information on the Master's application #### Language Requirements For an admission, you need to prove sufficient knowledge of the English language on CEFR level C1 (Common European Framework of Reference for Languages). Please note that you don't need a proof for German language proficiency (since the program is taught in English). Please find more details in this document: - English Language Skills M. Sc. Computer Science Please apply for this study program 9 months in advance. All applications will be evaluated after the respective deadlines: the results will be announced on the Campus-Management-Portal C@MPUS about 6-7 wee



- Original pre-check: agree — page says "you don't need a proof for German language proficiency (since the program is taught in English)".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S16](#s16)

### 34. university-of-stuttgart-m-sc-computer-science :: selection_process



- value: `"On the basis of the documents presented, the Board of Admission (Zulassungsausschuss) decides whether the conditions of entry are fulfilled or not. In case of the latter, an interview or an entrance examination may be necessary. In some cases, students who are missing certain qualifications may be granted admission on the condition that they acquire these qualifications in the course of their studies, for example by attending additional modules."`

- quote: "On the basis of the documents presented, the Board of Admission (Zulassungsausschuss) decides whether the conditions of entry are fulfilled or not. In case of the latter, an interview or an entrance examination may be necessary. In some cases, students who are missing certain qualifications may be granted admission on the condition that they acquire these qualifications in the course of their studies, for example by attending additional modules."

- doc: `de/ustutt/cs-msc/department`

- page excerpt:



  > puter Science - adequate knowledge of the English language for the special study: advanced knowledge of English at level C1 (recognized certificates e.g. TOEFL iBT score 95 or IELTS Band 7) For German students, the proof of 5 years of English classes at secondary school with final level C1 (Abitur) On the basis of the documents presented, the Board of Admission (Zulassungsausschuss) decides whether the conditions of entry are fulfilled or not. In case of the latter, an interview or an entrance examination may be necessary. In some cases, students who are missing certain qualifications may be granted admission on the condition that they acquire these qualifications in the course of their studies, for example by attending additional modules. In case of any further questions regarding the admissions requirements please contact us via e-mail. ### How to apply General information about the application for a Master program at the University of Stuttgart can be found on the web pages of the University . Please notice that if any document is



- Original pre-check: agree — verbatim from the department page ("the Board of Admission (Zulassungsausschuss) decides ... an interview or an entrance examination may be necessary"); the page also mentions a supplementary form used to "award admission points", which the value does not cover.

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S17](#s17)

### 35. university-of-stuttgart-m-sc-computer-science :: tuition_eur_per_semester_non_eu



- value: `1500.0`

- quote: "The Land Baden-Württemberg has introduced tuition fees for a second degree (650 EUR / semester) and for international students who are not citizens of an EU/EEA country (1500 EUR / semester)."

- doc: `de/ustutt/tuition-fees`

- page excerpt:



  > **# Fees and Charges An overview of the fees and charges which students of the University of Stuttgart have to pay. The Land Baden-Württemberg has introduced tuition fees for a second degree (650 EUR / semester) and for international students who are not citizens of an EU/EEA country (1500 EUR / semester). Further information is published here: Tuition fees for international students and for a second degree The following fees and charges are levied at the University of Stuttgart (the respective current legislations and fee statutes apply): ## Fees and Charges ### General fees (semester fee) | Adminis**



- Original pre-check: agree — page says "international students who are not citizens of an EU/EEA country (1500 EUR / semester)" and the table shows "Tuition fee for students from non-European countries | EUR 1500.00".

- auditor: [x] agree  [ ] disagree
- Scores: quote 1/1; narrow 1/1; strict 1/1.
- Verified source(s): [S18](#s18)

