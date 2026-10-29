# Phase 6 Step 0: programme rule coverage

Status: model-assisted draft, 2026-10-27; maintainer review pending. Generated from [coverage_inventory.json](../data/eligibility/coverage_inventory.json).

All 13 programmes and all 17 original fields are inventoried below. Classification describes the proposed automation boundary, not implemented rules or measured coverage. Every interpretation remains pending. See [the review packet](PHASE_6_RULE_REVIEW.md) and [five independent profiles](PHASE_6_FIVE_PROFILE_WORKSHEET.md).

`automatic`: deterministic comparisons against entered evidence are possible after rule review. `manual_review`: equivalence, ambiguity or required university assessment remains. `informational_readiness`: process, document, milestone or finance information, separate from academic admission. `not_published`: the original verified field is empty; this never implies exemption. Supplemental evidence can expose omissions without changing the original status.

Original values/quotes remain in the linked verified records. Source links identify the cached official snapshot, rather than asserting current live-page verification. Supporting citations are included. Rows with mixed behavior explain the numeric subchecks and the remaining review step.

## Programme counts

| Programme | Automatic | Information/readiness | Manual review | Not published |
|---|---:|---:|---:|---:|
| KIT M.Sc. Computational and Data Science | 2 | 2 | 2 | 11 |
| KIT M.Sc. Computer Science | 2 | 4 | 5 | 6 |
| RWTH Aachen M.Sc. Computer Science | 2 | 5 | 2 | 8 |
| RWTH Aachen M.Sc. Data Science | 1 | 6 | 2 | 8 |
| Saarland University M.Sc. Computer Science | 4 | 8 | 1 | 4 |
| Saarland University M.Sc. Data Science and Artificial Intelligence | 4 | 8 | 1 | 4 |
| TU Berlin M.Sc. Computer Science | 1 | 5 | 2 | 9 |
| TU Darmstadt M.Sc. Artificial Intelligence and Machine Learning | 2 | 6 | 3 | 6 |
| TU Darmstadt M.Sc. Computer Science | 2 | 7 | 3 | 5 |
| TU Dresden M.Sc. Computer Science | 1 | 7 | 2 | 7 |
| TUM M.Sc. Data Engineering and Analytics | 1 | 7 | 2 | 7 |
| TUM M.Sc. Informatics | 1 | 7 | 2 | 7 |
| University of Stuttgart M.Sc. Computer Science | 1 | 6 | 2 | 8 |
| **Total (221 fields)** | 24 | 78 | 29 | 90 |

## KIT — M.Sc. Computational and Data Science

[Verified values and original quotes](../data/verified/kit-m-sc-computational-and-data-science.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `3d726ca23a10879cfea8b8e0803ecaf52103a97d1e7239acd1f97dc4218faab2`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/kit/cds-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/kit/cds-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `manual_review` | 20 basic-maths LP AND (40 in one domain AND 12 in each remaining domain); 6-LP thesis additionally omitted. Overlap policy unresolved; <=12 missing LP requires committee approval. | [de/kit/cds-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php); [E05](PHASE_6_RULE_REVIEW.md#e05); [E06](PHASE_6_RULE_REVIEW.md#e06); [E07](PHASE_6_RULE_REVIEW.md#e07); [E08](PHASE_6_RULE_REVIEW.md#e08); [R01](PHASE_6_RULE_REVIEW.md#r01); [R03](PHASE_6_RULE_REVIEW.md#r03) |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | Record has test routes; cache additionally states school/sole-English-degree evidence. IELTS6.5/components5.5; other per-test components; proof by enrolment and unlimited test validity. | [de/kit/cds-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php); [E40](PHASE_6_RULE_REVIEW.md#e40); [E41](PHASE_6_RULE_REVIEW.md#e41); [E43](PHASE_6_RULE_REVIEW.md#e43); [R04](PHASE_6_RULE_REVIEW.md#r04) |
| `entrance_tests` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `not_published` | Record is not_published; cached programme describes discretionary conditional admission. Pending interpretation, not an exemption. | [E07](PHASE_6_RULE_REVIEW.md#e07); [E08](PHASE_6_RULE_REVIEW.md#e08); [R03](PHASE_6_RULE_REVIEW.md#r03) |
| `required_documents` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/kit/tuition-fees](https://www.intl.kit.edu/istudies/12606.php); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/kit/cds-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php) |

## KIT — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/kit-m-sc-computer-science.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `ea85986cefb22fe0ac7c50ecaea561f4fa171997f7e02f3f0fcd8b741917fbb2`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `manual_review` | Direct route: theory 15, practical 30, engineering 8, maths 25 CP. Alternative GATE/interview routes mean a failed direct-credit comparison alone cannot reject. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [R01](PHASE_6_RULE_REVIEW.md#r01); [R02](PHASE_6_RULE_REVIEW.md#r02) |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `manual_review` | Top-10% evidence belongs to the interview route, not every applicant. | [de/kit/cs-msc/admission](https://www.informatik.kit.edu/english/14346.php); [E04](PHASE_6_RULE_REVIEW.md#e04); [R02](PHASE_6_RULE_REVIEW.md#r02) |
| `english` | `automatic` | B2 evidence alternatives include supported school/English-degree routes. IELTS6.5 AND every section>=5.5; other tests have their own components. Due at enrolment; listed English tests have unlimited validity. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [E42](PHASE_6_RULE_REVIEW.md#e42); [R04](PHASE_6_RULE_REVIEW.md#r04) |
| `entrance_tests` | `manual_review` | GRE VR151/QR164/AW4 OR qualifying CS/DA GATE, with EHEA/Lisbon degree exemptions; separate from selection-route alternatives. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [E02](PHASE_6_RULE_REVIEW.md#e02); [E03](PHASE_6_RULE_REVIEW.md#e03); [R02](PHASE_6_RULE_REVIEW.md#r02); [R04](PHASE_6_RULE_REVIEW.md#r04); [R06](PHASE_6_RULE_REVIEW.md#r06) |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Calendar comparison is deterministic after route/class/milestone/year-offset review; keep separate from academic eligibility. | [de/kit/cs-msc/admission](https://www.informatik.kit.edu/english/14346.php); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `manual_review` | GATE OR direct credits OR passed interview; relaxed 15/20/6/20 in at least three areas plus rank before interview. Ranking is not an admission probability. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php); [E01](PHASE_6_RULE_REVIEW.md#e01); [E04](PHASE_6_RULE_REVIEW.md#e04); [R02](PHASE_6_RULE_REVIEW.md#r02) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/kit/cs-msc/department](https://www.informatik.kit.edu/english/mastercomputerscience.php); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/kit/tuition-fees](https://www.intl.kit.edu/istudies/12606.php); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/kit/cs-msc/programme](https://www.sle.kit.edu/english/vorstudium/master-computer-science.php) |

## RWTH Aachen — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/rwth-aachen-m-sc-computer-science.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `c4cf2e21fa8f8f52204fb3e33844ac6b06f92041822bff236fb0016b81d8f627`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/rwth/cs-msc/department](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/~npqg/master-informatik/?lidx=1); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `manual_review` | Record lists TOEFL90/4.5 or IELTS6.0 etc.; PDF has two English lists and programme section references. Resolve visual section scope and enrolment milestone before positive verdict. | [de/rwth/language-requirements-pdf](https://www.rwth-aachen.de/global/show_document.asp?id=aaaaaaaaabpixuo); [E13](PHASE_6_RULE_REVIEW.md#e13); [E14](PHASE_6_RULE_REVIEW.md#e14); [R07](PHASE_6_RULE_REVIEW.md#r07) |
| `entrance_tests` | `automatic` | Degree outside EU triggers GRE; otherwise QR>75th, VR>15th percentiles AND AW>=3.5. | [de/rwth/cs-msc/application](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/master-informatik/~npsy/bewerbungsverfahren/?lidx=1); [E09](PHASE_6_RULE_REVIEW.md#e09); [R05](PHASE_6_RULE_REVIEW.md#r05); [R06](PHASE_6_RULE_REVIEW.md#r06) |
| `german` | `automatic` | Accepted German proof at C1 due by enrolment; a self-reported level alone is not an accepted certificate. | [de/rwth/cs-msc/application](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/master-informatik/~npsy/bewerbungsverfahren/?lidx=1); [R07](PHASE_6_RULE_REVIEW.md#r07) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/rwth/cs-msc/application](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/master-informatik/~npsy/bewerbungsverfahren/?lidx=1); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter March1/non-EU vs July15/EU; summer September1(Y-1) vs January15(Y). RWTH enrolment or relevant German degree changes non-EU deadline; DS names EEA too. | [de/rwth/application-deadlines](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/~bsottx/bewerbungs-und-einschreibefrist/?lidx=1); [E11](PHASE_6_RULE_REVIEW.md#e11); [E12](PHASE_6_RULE_REVIEW.md#e12); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/rwth/cs-msc/department](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/~npqg/master-informatik/?lidx=1); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/rwth/master-application-international](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/bewerbung-um-einen-studienplatz/master-bewerbung/~dqml/bewerbung-master-internationale/?lidx=1); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/rwth/cs-msc/programme](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/studiengaenge/liste-aktuelle-studiengaenge/studiengangbeschreibung/~bcfg/informatik-m-sc/?lidx=1) |

## RWTH Aachen — M.Sc. Data Science

[Verified values and original quotes](../data/verified/rwth-aachen-m-sc-data-science.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `09f2c8e081e0830a38692bb8f3020e6c063c6b5a4ab257103bae03232ad1830f`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Recognised degree AND one of CS/maths/physics module profiles; exact published RWTH reference degrees can resolve the profile route, foreign equivalence stays review. | [de/rwth/ds-msc/application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `manual_review` | Record lists TOEFL90/4.5 or IELTS6.0 etc.; PDF has two English lists and programme section references. Resolve visual section scope and enrolment milestone before positive verdict. | [de/rwth/language-requirements-pdf](https://www.rwth-aachen.de/global/show_document.asp?id=aaaaaaaaabpixuo); [E13](PHASE_6_RULE_REVIEW.md#e13); [E14](PHASE_6_RULE_REVIEW.md#e14); [R07](PHASE_6_RULE_REVIEW.md#r07) |
| `entrance_tests` | `automatic` | Citizenship EU/EEA OR qualifying German secondary schooling exempts GRE; otherwise QR>75th, VR>15th percentiles AND AW>=3.5. | [de/rwth/ds-msc/application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/); [E10](PHASE_6_RULE_REVIEW.md#e10); [R05](PHASE_6_RULE_REVIEW.md#r05); [R06](PHASE_6_RULE_REVIEW.md#r06) |
| `german` | `informational_readiness` | Source explicitly says no German proof is needed at the stated milestone; display exemption without counting a passed requirement. | [de/rwth/ds-msc/requirements](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/rwth/ds-msc/application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter March1/non-EU vs July15/EU; summer September1(Y-1) vs January15(Y). RWTH enrolment or relevant German degree changes non-EU deadline; DS names EEA too. | [de/rwth/ds-msc/application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/); [E11](PHASE_6_RULE_REVIEW.md#e11); [E12](PHASE_6_RULE_REVIEW.md#e12); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/rwth/ds-msc/application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/rwth/master-application-international](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/bewerbung-um-einen-studienplatz/master-bewerbung/~dqml/bewerbung-master-internationale/?lidx=1); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/rwth/ds-msc/programme](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/studiengaenge/liste-aktuelle-studiengaenge/studiengangbeschreibung/~pzpc/data-science-m-sc/?lidx=1) |

## Saarland University — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/saarland-university-m-sc-computer-science.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `7dddd9fb5d34a431b215b29b75e62621ce5f75b2fa1e678f0c86407e9bea5d56`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `automatic` | (>=75% OR >=3.00/4 on the applicable original scale) AND top10% rank; no invented German-grade threshold. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E19](PHASE_6_RULE_REVIEW.md#e19); [R09](PHASE_6_RULE_REVIEW.md#r09) |
| `english` | `automatic` | IELTS7; TOEFL95/120 or new5/6, PBT600/677 subject to format-scope review; named Cambridge/PTE76. Home/expired tests allowed; MOI disallowed; narrow native/in-person-study exceptions. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E22](PHASE_6_RULE_REVIEW.md#e22); [E23](PHASE_6_RULE_REVIEW.md#e23); [E24](PHASE_6_RULE_REVIEW.md#e24); [R10](PHASE_6_RULE_REVIEW.md#r10) |
| `entrance_tests` | `automatic` | GRE General OR Indian GATE result without numeric cutoff; exempt by degree earned in EHEA/Switzerland/UK, not non-EHEA branch campuses. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E20](PHASE_6_RULE_REVIEW.md#e20); [E21](PHASE_6_RULE_REVIEW.md#e21); [R06](PHASE_6_RULE_REVIEW.md#r06); [R10](PHASE_6_RULE_REVIEW.md#r10) |
| `german` | `informational_readiness` | Source explicitly says no German proof is needed at the stated milestone; display exemption without counting a passed requirement. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `informational_readiness` | Document readiness uses qualifying-degree country, not citizenship; missing proof is a readiness gap. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/saarland/cs-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/informatics.html); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter final May15(Y), early November15(Y-1); summer final November15(Y-1), early May15(Y-1). Early rounds are optional. | [de/saarland/cs-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/informatics.html); [E25](PHASE_6_RULE_REVIEW.md#e25); [E26](PHASE_6_RULE_REVIEW.md#e26); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [de/saarland/cs-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/informatics.html); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/saarland/cs-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/informatics.html); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/) |

## Saarland University — M.Sc. Data Science and Artificial Intelligence

[Verified values and original quotes](../data/verified/saarland-university-m-sc-data-science-and-artificial-intelligence.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `d2322b7af0d71ef930eafb2d0b20276153730814691446dbefd25f87d0ff0c8f`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/saarland/dsai-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/data-science.html); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/saarland/dsai-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/data-science.html); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `automatic` | (>=75% OR >=3.00/4 on the applicable original scale) AND top10% rank; no invented German-grade threshold. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E19](PHASE_6_RULE_REVIEW.md#e19); [R09](PHASE_6_RULE_REVIEW.md#r09) |
| `english` | `automatic` | IELTS7; TOEFL95/120 or new5/6, PBT600/677 subject to format-scope review; named Cambridge/PTE76. Home/expired tests allowed; MOI disallowed; narrow native/in-person-study exceptions. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E22](PHASE_6_RULE_REVIEW.md#e22); [E23](PHASE_6_RULE_REVIEW.md#e23); [E24](PHASE_6_RULE_REVIEW.md#e24); [R10](PHASE_6_RULE_REVIEW.md#r10) |
| `entrance_tests` | `automatic` | GRE General OR Indian GATE result without numeric cutoff; exempt by degree earned in EHEA/Switzerland/UK, not non-EHEA branch campuses. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [E20](PHASE_6_RULE_REVIEW.md#e20); [E21](PHASE_6_RULE_REVIEW.md#e21); [R06](PHASE_6_RULE_REVIEW.md#r06); [R10](PHASE_6_RULE_REVIEW.md#r10) |
| `german` | `informational_readiness` | Source explicitly says no German proof is needed at the stated milestone; display exemption without counting a passed requirement. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `informational_readiness` | Document readiness uses qualifying-degree country, not citizenship; missing proof is a readiness gap. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter final May15(Y), early November15(Y-1); summer final November15(Y-1), early May15(Y-1). Early rounds are optional. | [de/saarland/dsai-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/data-science.html); [E25](PHASE_6_RULE_REVIEW.md#e25); [E26](PHASE_6_RULE_REVIEW.md#e26); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/saarland/masters-application-guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/saarland/dsai-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/data-science.html); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/saarland/dsai-msc/programme](https://www.uni-saarland.de/en/study/programmes/master/data-science.html) |

## TU Berlin — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/tu-berlin-m-sc-computer-science.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `abf4441514dbbeb90cccbf878d66db024bcea1672e7d50cbb17ed826f452feb5`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tub/cs-msc/application](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `manual_review` | 36 foundations CP includes theory12+engineering12+practical12; plus maths18 and additionalCS30 excluding thesis. Respect theory exclusions and board allocation. | [de/tub/cs-msc/application](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission); [E27](PHASE_6_RULE_REVIEW.md#e27); [R01](PHASE_6_RULE_REVIEW.md#r01); [R12](PHASE_6_RULE_REVIEW.md#r12) |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | Faculty IV higher B2: IELTS>=6.5; only listed native-country degree proof. Other accepted-certificate branches are not fully cached. No generic MOI substitution. | [de/tub/eecs-application-faq](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/application-admission-faq); [E28](PHASE_6_RULE_REVIEW.md#e28); [R12](PHASE_6_RULE_REVIEW.md#r12) |
| `entrance_tests` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `informational_readiness` | Published not-required statement; experience cannot substitute for academic prerequisites. | [de/tub/cs-msc/programme](https://www.tu.berlin/en/studying/study-programs/all-programs-offered/study-course/computer-science-informatik-m-sc); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | German-degree direct route; foreign-degree VPD via uni-assist from summer2026 plus university application, not two interchangeable portals. | [de/tub/cs-msc/application](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission); [E29](PHASE_6_RULE_REVIEW.md#e29); [R12](PHASE_6_RULE_REVIEW.md#r12); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R11](PHASE_6_RULE_REVIEW.md#r11); [R12](PHASE_6_RULE_REVIEW.md#r12) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/tub/cs-msc/application](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/tub/eecs-application-faq](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/application-admission-faq); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tub/cs-msc/programme](https://www.tu.berlin/en/studying/study-programs/all-programs-offered/study-course/computer-science-informatik-m-sc) |

## TU Darmstadt — M.Sc. Artificial Intelligence and Machine Learning

[Verified values and original quotes](../data/verified/tu-darmstadt-m-sc-artificial-intelligence-and-machine-learning.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `22bfc9865e47f439e949a6dbd78e9fd3eda2a31eac6d0a382f8bdb75bbaead42`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `manual_review` | >=60 ECTS must match reference Informatik core in content, academic level and depth; an entered 60 is not certified equivalence. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | IELTS>=7 OR TOEFLiBT>=95 OR official entire-Bachelor English instruction confirmation; no cross-format TOEFL conversion. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `entrance_tests` | `manual_review` | Conditional competency exam; optional GRE155/165/3.5 or GATE750 exemption by Aug20/Feb20. Preserve academic equivalence, same sitting and submission evidence separately. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E15](PHASE_6_RULE_REVIEW.md#e15); [E16](PHASE_6_RULE_REVIEW.md#e16); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `informational_readiness` | Published not-required statement; experience cannot substitute for academic prerequisites. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter July15(Y), summer January15(Y): both online cutoff and hard-copy arrival. GRE/GATE exemption deadlines Aug20/Feb20 are separate. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E17](PHASE_6_RULE_REVIEW.md#e17); [R08](PHASE_6_RULE_REVIEW.md#r08); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/tu-darmstadt/aiml-msc/programme](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334592.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `not_published` | Record is not_published; shared official guide requires hard-copy application/documents. Pending correction review. | [E17](PHASE_6_RULE_REVIEW.md#e17); [R08](PHASE_6_RULE_REVIEW.md#r08); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | EUR348.18 is explicitly summer2025; historical information cannot certify a 2026/2027 payable contribution. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E18](PHASE_6_RULE_REVIEW.md#e18); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tu-darmstadt/aiml-msc/programme](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334592.en.jsp) |

## TU Darmstadt — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/tu-darmstadt-m-sc-computer-science.json); tier `human`; semantic review `pending`.

Canonical record SHA-256: `b87f9260300eb3c064033b3fdd76663bcaf6c373bc1a928bb9b53bb9e8759c17`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tu-darmstadt/cs-msc/programme](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334656.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `automatic` | Compare the published total against confirmed ECTS only; an equivalent-workload claim or other credit unit needs review. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `subject_credits` | `manual_review` | >=60 ECTS must match reference Informatik core in content, academic level and depth; an entered 60 is not certified equivalence. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | IELTS>=7 OR TOEFLiBT>=95 OR official entire-Bachelor English instruction confirmation; no cross-format TOEFL conversion. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `entrance_tests` | `manual_review` | Conditional competency exam; optional GRE155/165/3.5 or GATE750 exemption by Aug20/Feb20. Preserve academic equivalence, same sitting and submission evidence separately. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E15](PHASE_6_RULE_REVIEW.md#e15); [E16](PHASE_6_RULE_REVIEW.md#e16); [R08](PHASE_6_RULE_REVIEW.md#r08) |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `informational_readiness` | Published not-required statement; experience cannot substitute for academic prerequisites. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Winter July15(Y), summer January15(Y): both online cutoff and hard-copy arrival. GRE/GATE exemption deadlines Aug20/Feb20 are separate. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E17](PHASE_6_RULE_REVIEW.md#e17); [R08](PHASE_6_RULE_REVIEW.md#r08); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `informational_readiness` | Describe the published selection process; routine board selection alone is not an additional unresolved hard prerequisite. | [de/tu-darmstadt/cs-msc/programme](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334656.en.jsp); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | EUR348.18 is explicitly summer2025; historical information cannot certify a 2026/2027 payable contribution. | [de/tu-darmstadt/informatics-master-admission-guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp); [E18](PHASE_6_RULE_REVIEW.md#e18); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tu-darmstadt/cs-msc/programme](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334656.en.jsp) |

## TU Dresden — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/tu-dresden-m-sc-computer-science.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `3c7460d2e1249d4929184c6d70ca649ebd091e58807fc7e653ca918376a11487`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tud/cs-msc/programme](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_studiengang?autoid=73&set_language=en); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | IELTS>=7 OR TOEFL95 old scale /5.0 new scale; explicit new-scale evidence is missing from the existing record. C1 claim alone does not identify proof. | [de/tud/cs-msc/aptitude-assessment](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_eignungsfeststellung_detail?autoid=73&set_language=en); [E30](PHASE_6_RULE_REVIEW.md#e30); [R13](PHASE_6_RULE_REVIEW.md#r13) |
| `entrance_tests` | `not_published` | Record is not_published; selection_process explicitly requires university aptitude assessment. | [R13](PHASE_6_RULE_REVIEW.md#r13) |
| `german` | `informational_readiness` | Source explicitly says no German proof is needed at the stated milestone; display exemption without counting a passed requirement. | [de/tud/international-faq](https://tu-dresden.de/studium/vor-dem-studium/internationales/faq?set_language=en) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `informational_readiness` | Document readiness uses qualifying-degree country, not citizenship; missing proof is a readiness gap. | [de/tud/international-faq](https://tu-dresden.de/studium/vor-dem-studium/internationales/faq?set_language=en); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | German-degree aptitude-registration portal vs foreign-degree uni-assist application; keep distinct from enrolment. | [de/tud/cs-msc/aptitude-assessment](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_eignungsfeststellung_detail?autoid=73&set_language=en); [E31](PHASE_6_RULE_REVIEW.md#e31); [R13](PHASE_6_RULE_REVIEW.md#r13) |
| `deadlines` | `informational_readiness` | Foreign-degree non-EU: May31(Y)/Nov30(Y-1); foreign-degree EU: July15(Y)/Jan15(Y). German-degree aptitude registration June1-July15 /Dec1(Y-1)-Jan15. | [de/tud/cs-msc/aptitude-assessment](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_eignungsfeststellung_detail?autoid=73&set_language=en); [E31](PHASE_6_RULE_REVIEW.md#e31); [R11](PHASE_6_RULE_REVIEW.md#r11); [R13](PHASE_6_RULE_REVIEW.md#r13) |
| `selection_process` | `manual_review` | Required university aptitude outcome; not_published entrance_tests is not an exemption from this assessment. | [de/tud/cs-msc/programme](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_studiengang?autoid=73&set_language=en); [R01](PHASE_6_RULE_REVIEW.md#r01); [R13](PHASE_6_RULE_REVIEW.md#r13) |
| `required_documents` | `informational_readiness` | Track supplied/pending/absent documents using sourced conditions; preserve optional items. | [de/tud/cs-msc/aptitude-assessment](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_eignungsfeststellung_detail?autoid=73&set_language=en); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | EUR361 applies to winter2026/27 and the stated attendance category; not a timeless contribution. | [de/tud/semester-contribution](https://tu-dresden.de/studium/im-studium/studienorganisation/rueckmeldung); [E44](PHASE_6_RULE_REVIEW.md#e44); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tud/cs-msc/programme](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_studiengang?autoid=73&set_language=en) |

## TUM — M.Sc. Data Engineering and Analytics

[Verified values and original quotes](../data/verified/tum-m-sc-data-engineering-and-analytics.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `f180521a23fe26d9181c96a015adfb8efe1ff46c6010a19522051795c4e19230`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `not_published` | Record is not_published; cached programme explicitly requires English proof. Accepted thresholds are not covered by the cached language page; mandatory source gap. | [E35](PHASE_6_RULE_REVIEW.md#e35); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `entrance_tests` | `automatic` | Degree in Bangladesh/China/India/Iran/Pakistan: GRE QR>=164 AND AW>=4 OR annual qualifying CS GATE; use explicit scorecard qualification, not an invented cutoff. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `informational_readiness` | Document readiness uses qualifying-degree country, not citizenship; missing proof is a readiness gap. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | University application plus VPD for qualifying degree outside Germany; VPD alone is not an application. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R14](PHASE_6_RULE_REVIEW.md#r14); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Final winterMay31(Y)/summerNov30(Y-1); keep visa recommendation and period-specific assessment dates separate. | [de/tum/dea-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/data-engineering-and-analytics-master-of-science-msc); [R11](PHASE_6_RULE_REVIEW.md#r11); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `selection_process` | `manual_review` | University two-stage aptitude assessment/equivalence remains unresolved; programme interview narrative and department test detail need reconciliation. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R01](PHASE_6_RULE_REVIEW.md#r01); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `required_documents` | `informational_readiness` | Preserve degree-country VPD/GRE/APS/language conditions and optional training certificates; essay/motivation authorship is the student’s responsibility. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/); [R14](PHASE_6_RULE_REVIEW.md#r14); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/tum/dea-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/data-engineering-and-analytics-master-of-science-msc); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | Cited EUR/semester contribution valid only for its source period; separate from tuition/living costs. | [de/tum/dea-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/data-engineering-and-analytics-master-of-science-msc); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tum/dea-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/) |

## TUM — M.Sc. Informatics

[Verified values and original quotes](../data/verified/tum-m-sc-informatics.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `b67527c84ef26cfa5b7023fbc2c48784e0bf14b9d1bd94fd1b5d3f55aff1b2a4`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/tum/informatics-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `not_published` | Record is not_published; cached programme explicitly requires English proof. Accepted thresholds are not covered by the cached language page; mandatory source gap. | [E36](PHASE_6_RULE_REVIEW.md#e36); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `entrance_tests` | `automatic` | Degree in Bangladesh/China/India/Iran/Pakistan: GRE QR>=164 AND AW>=4 OR annual qualifying CS GATE; use explicit scorecard qualification, not an invented cutoff. | [de/tum/informatics-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `german` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `informational_readiness` | Document readiness uses qualifying-degree country, not citizenship; missing proof is a readiness gap. | [de/tum/informatics-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | University application plus VPD for qualifying degree outside Germany; VPD alone is not an application. | [de/tum/informatics-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/); [R14](PHASE_6_RULE_REVIEW.md#r14); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | Final winterMay31(Y)/summerNov30(Y-1); keep visa recommendation and period-specific assessment dates separate. | [de/tum/informatics-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc); [E32](PHASE_6_RULE_REVIEW.md#e32); [E33](PHASE_6_RULE_REVIEW.md#e33); [R11](PHASE_6_RULE_REVIEW.md#r11); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `selection_process` | `manual_review` | University two-stage aptitude assessment/equivalence remains unresolved; programme interview narrative and department test detail need reconciliation. | [de/tum/informatics-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc); [E34](PHASE_6_RULE_REVIEW.md#e34); [R01](PHASE_6_RULE_REVIEW.md#r01); [R14](PHASE_6_RULE_REVIEW.md#r14) |
| `required_documents` | `informational_readiness` | Preserve degree-country VPD/GRE/APS/language conditions and optional training certificates; essay/motivation authorship is the student’s responsibility. | [de/tum/informatics-msc/department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/); [R14](PHASE_6_RULE_REVIEW.md#r14); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/tum/informatics-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | Cited EUR/semester contribution valid only for its source period; separate from tuition/living costs. | [de/tum/informatics-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/tum/informatics-msc/programme](https://www.tum.de/en/studies/degree-programs/detail/informatics-master-of-science-msc) |

## University of Stuttgart — M.Sc. Computer Science

[Verified values and original quotes](../data/verified/university-of-stuttgart-m-sc-computer-science.json); tier `second_pass`; semantic review `pending`.

Canonical record SHA-256: `430b7664c0bc143e8a08fde7f0a1b9ae16e192bdbe8d1aa608a5201f5ef2695c`.

| Original field | Classification | Comparison / boundary | Evidence and review |
|---|---|---|---|
| `degree_requirement` | `manual_review` | Degree, duration and subject equivalence require the published reference qualification or university assessment; compare entered facts separately. | [de/ustutt/cs-msc/programme](https://www.uni-stuttgart.de/en/study/study-programs/Computer-Science-M.Sc.-00001/); [R01](PHASE_6_RULE_REVIEW.md#r01) |
| `min_total_ects` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `subject_credits` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_german_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `min_grade_original_scale` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `english` | `automatic` | IELTS Academic7; TOEFL95 old/>=5 new; named Cambridge/Oxford/PTE76/telc results. Valid through deadline; MOI excluded; citizenship AND education exception with Quebec exclusion. | [de/ustutt/cs-msc/english-proofs](https://www.uni-stuttgart.de/studium/studienangebot_assets/computer-science/pdf/English_language_skills_MSc_CS_barrierefrei_01-2026.pdf); [E37](PHASE_6_RULE_REVIEW.md#e37); [E38](PHASE_6_RULE_REVIEW.md#e38); [E39](PHASE_6_RULE_REVIEW.md#e39); [R15](PHASE_6_RULE_REVIEW.md#r15) |
| `entrance_tests` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `german` | `informational_readiness` | Source explicitly says no German proof is needed at the stated milestone; display exemption without counting a passed requirement. | [de/ustutt/cs-msc/programme](https://www.uni-stuttgart.de/en/study/study-programs/Computer-Science-M.Sc.-00001/) |
| `work_experience` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | — |
| `aps_degree_countries` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `application_route` | `informational_readiness` | Show published route and conditional portal/VPD steps, with a separate readiness summary. | [de/ustutt/cs-msc/department](https://www.f05.uni-stuttgart.de/en/cs/prospective-students/msc-computerscience/); [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `deadlines` | `informational_readiness` | WinterJanuary15(Y); summerJuly15(Y-1). These early final dates are not the usual July/January convention. | [de/ustutt/cs-msc/programme](https://www.uni-stuttgart.de/en/study/study-programs/Computer-Science-M.Sc.-00001/); [R11](PHASE_6_RULE_REVIEW.md#r11) |
| `selection_process` | `manual_review` | Unresolved qualification gaps may trigger interview/exam or committee-approved conditions; do not infer an outcome. | [de/ustutt/cs-msc/department](https://www.f05.uni-stuttgart.de/en/cs/prospective-students/msc-computerscience/); [R01](PHASE_6_RULE_REVIEW.md#r01); [R15](PHASE_6_RULE_REVIEW.md#r15) |
| `required_documents` | `not_published` | Not published in the verified field; this does not establish absence or exemption. | [R16](PHASE_6_RULE_REVIEW.md#r16) |
| `tuition_eur_per_semester_non_eu` | `informational_readiness` | Cited EUR/semester amount; fee liability, exceptions and waivers require evidence; separate from visa proof. | [de/ustutt/tuition-fees](https://www.student.uni-stuttgart.de/en/organizing-studies/formalities/tuition-and-fees/); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `semester_fee_eur` | `informational_readiness` | Cited EUR/semester contribution valid only for its source period; separate from tuition/living costs. | [de/ustutt/tuition-fees](https://www.student.uni-stuttgart.de/en/organizing-studies/formalities/tuition-and-fees/); [R17](PHASE_6_RULE_REVIEW.md#r17) |
| `language_of_instruction` | `informational_readiness` | Teaching language is information; it does not itself prove the applicant holds accepted language evidence. | [de/ustutt/cs-msc/department](https://www.f05.uni-stuttgart.de/en/cs/prospective-students/msc-computerscience/) |

## Snapshot bindings

The inventory locks raw-byte hashes for 51 Phase 4 inputs, canonical original-record hashes for 13 programmes, and raw/cleaned snapshot hashes for 42 source documents. No extraction record, verification tier, audit score, retrieval label or benchmark is changed.

Run `make validate-phase6-inventory` for identities, bindings and rendered-document consistency. Run `make validate-phase6-inventory ARGS="--check-cache"` locally to also validate raw/cleaned snapshot hashes and every original/supplemental quote. The default check does not claim raw-page or live-page verification. To explicitly regenerate the Markdown after editing the draft inventory, run `.venv/bin/python scripts/validate_phase6_inventory.py --render`.
