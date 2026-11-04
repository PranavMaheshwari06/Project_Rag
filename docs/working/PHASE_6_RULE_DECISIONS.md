# Phase 6 Step 3: rule decisions for 11 programmes

One decision round for the rule files of the 11 programmes that had none. Each
item says how the engine reads a published requirement. Nothing here changes a
verified record; accepting an item only marks that rule as reviewed by the
maintainer.

**How to answer** (one message): `accept all except X2, D05, D21` and, for each
exception, `correct` with the fix in a sentence or `defer` (the rule stays pending).
Where an item offers options, name the option: `X2: b`.

Shared meanings:
- **"The university decides"**: the engine shows the requirement and never says
  it is met. A student can still be told "does not meet" by other rules.
- **Readiness**: needed later (enrolment, visa), shown as a to-do; it never
  changes the admission verdict.
- Every programme keeps a hard "the university decides whether your degree is
  equivalent" rule, so **no programme can show a positive verdict yet** (see X1).

Pages: RWTH [CS application](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/master-informatik/~npsy/bewerbungsverfahren/?lidx=1),
[CS department](https://www.informatik.rwth-aachen.de/cms/informatik/studium/vor-dem-studium/bewerbungsinfos/~npqg/master-informatik/?lidx=1),
[DS application](https://sc.informatik.rwth-aachen.de/en/studium/master/master-data-science/application-for-admission/),
[languages](https://www.rwth-aachen.de/cms/root/studium/vor-dem-studium/zugangsvoraussetzungen/~zwyn/sprachkenntnisse/?lidx=1),
[language PDF](https://www.rwth-aachen.de/global/show_document.asp?id=aaaaaaaaabpixuo) ·
Saarland [application guide](https://saarland-informatics-campus.de/en/studium-studies/master-english/application-guide/) ·
TU Darmstadt [CS](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334656.en.jsp),
[AIML](https://www.tu-darmstadt.de/studieren/studieninteressierte/studienangebot_studiengaenge/studiengang_334592.en.jsp),
[admission guide](https://www.informatik.tu-darmstadt.de/studium_fb20/vor_dem_studium/bewerbung_1/bewerbung_2.en.jsp) ·
TUM DEA [department](https://www.cit.tum.de/en/cit/studies/degree-programs/master-data-engineering-and-analytics/),
[languages](https://www.tum.de/en/studies/application/application-info-portal/admission-requirements/language-certificates) ·
KIT CDS [programme](https://www.sle.kit.edu/english/vorstudium/master-computational-data-science.php) ·
TU Berlin [CS application](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/masters-programs/msc-computer-science-informatik/msc-cs-in-application-admission),
[FAQ](https://www.tu.berlin/en/eecs/academics-teaching/study-offer/application-admission-faq) ·
TU Dresden [programme](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_studiengang?autoid=73&set_language=en),
[aptitude](https://tu-dresden.de/studium/vor-dem-studium/studienangebot/sins/sins_eignungsfeststellung_detail?autoid=73&set_language=en),
[international FAQ](https://tu-dresden.de/studium/vor-dem-studium/internationales/faq?set_language=en) ·
Stuttgart [programme](https://www.uni-stuttgart.de/en/study/study-programs/Computer-Science-M.Sc.-00001/),
[department](https://www.f05.uni-stuttgart.de/en/cs/prospective-students/msc-computerscience/),
[English PDF](https://www.uni-stuttgart.de/studium/studienangebot_assets/computer-science/pdf/English_language_skills_MSc_CS_barrierefrei_01-2026.pdf).

## 1. Cross-cutting questions (answer these first)

**X1. A "the university confirmed my degree equivalence" answer in the profile.**
Without it no programme can ever show "meets the checked requirements".
Recommend: **accept**. The student ticks it only after receiving the university's
assessment, and it is added before Step 5.

**X2. TOEFL's new 1-6 scale (2026).** Saarland (5), Dresden (5.0), Stuttgart (5)
and RWTH (4.5) publish a new-scale minimum. Today Dresden and Stuttgart treat it
as a separate test ("TOEFL iBT (2026 scale)"), Saarland sends any TOEFL score of
6 or less to the university, and RWTH does not model it.
(a) Use the separate test everywhere a page gives a new-scale minimum.
(b) Leave as is.
Recommend **a**: one convention, and a new-scale score can then pass or fail.

**X3. Credits in a unit other than ECTS.** Today KIT CS and KIT CDS say "does
not meet" for any other unit, while Darmstadt and Saarland say "the university
decides". Recommend **"the university decides" everywhere**: the engine does not
convert units, so a fail would be invented. KIT CS and KIT CDS would change.

**X4. "Other proof may be accepted".** A rule gets a "the university decides"
fallback for English only where the page itself says other proof may count
(TUM, KIT, RWTH, TU Berlin, Dresden). Where the page gives a closed list
(Darmstadt, Saarland, Stuttgart), failing every listed proof is "does not meet".
Recommend: **accept**.

## 2. Interpretation decisions, per university

### RWTH Aachen (Computer Science, Data Science)

**D01 · RWTH CS · GRE only for a first degree from outside the EU.** It needs
Quantitative above the 75th percentile, Verbal above the 15th percentile (both
"above": exactly 75 fails) and Writing at least 3.5.
Source: de/rwth/cs-msc/application "if your first degree is from outside the European Union, you are required to submit a GRE test certificate".
Assumed: "EU" means the 27 EU states, so UK, Swiss and Norwegian degrees need
the GRE. There is no GATE alternative (none is named).
University decides: nothing. Recommend: accept.

**D02 · RWTH CS · English and German (C1) are needed to enrol, not to be
admitted.** They are shown as to-dos and never block the verdict. German C1 or
C2 meets; RWTH decides the exemptions (German schooling or degree, bilingual IB,
Austrian degree).
Source: de/rwth/cs-msc/application "After a successful application, you still have submit proof of German and English language proficiency."
Recommend: accept.

**D03 · RWTH CS and DS · English list.** It accepts TOEFL iBT 90, IELTS 6.0,
Cambridge B2 First grade A or B, C1 Advanced or C2 Proficiency (grade A-C or
"pass"), PTE Academic 60, or UNIcert II or higher. A degree or school diploma
from the UK, Ireland, Australia, New Zealand, Canada or the US exempts;
citizenship does not.
Source: de/rwth/language-requirements-pdf "b) IELTS test with a score of at least 6.0"; de/rwth/language-requirements "high school diploma or academic degree in an English-speaking country are exempt".
Assumed: both programmes use the PDF's 90 / 6.0 list (checked on the rendered
PDF), not its 100 / 7.0 list.
University decides: other comparable evidence (an English-taught bachelor's
thesis, a school certificate at B2), so English never shows "does not meet".
Recommend: accept.

**D04 · RWTH DS · The three module profiles (CS, Maths, Physics) are one hard
"RWTH decides" rule.** No profile fact holds module contents.
Source: de/rwth/ds-msc/application "one of the profiles mentioned below must be fulfilled".
Recommend: accept.

**D05 · RWTH DS · GRE exemption for EU/EEA citizens and German school leavers.**
This was left out for now (earlier decision). The consequence: for DS a low GRE
shows "RWTH decides", never "does not meet", even for a student who is clearly
not exempt.
Options: (a) keep. (b) Build it from existing facts: citizenship in the EU or
Iceland, Liechtenstein or Norway, or school country Germany, exempts. A known
non-exempt student then needs the GRE, and an unknown stays unknown.
Source: de/rwth/ds-msc/application "The GRE is not required for applicants with citizenship of the European Union or European Economic Area or who completed their secondary education in Germany".
Recommend **b**: small, uses facts the profile already has, and gives a real
answer to most applicants.

**D06 · RWTH DS · English is an admission requirement** (unlike CS), because it
is listed among the formal entrance requirements. Medium-of-instruction letters
are not used ("in general not accepted"). Recommend: accept.

### Saarland University (Computer Science, Data Science and AI)

Both programmes use one application guide and get identical rules, except that
DSAI also names machine learning, AI and data mining as expected background.

**D07 · Degree credits.** A German bachelor's needs 180 ECTS. A foreign degree
only has to be "equivalent", so a short credit total is "Saarland decides",
never a fail.
Source: "Bachelor's degree from a German university (at least 180 CP) or an equivalent qualification from a foreign university".
Recommend: accept (it differs from KIT, where 180 is stated for everyone).

**D08 · Grade.** At least 75 % on a percentage scale, or at least 3.00 on a
4-point scale. Any other scale (for example a 10-point CGPA) is "Saarland
decides".
Option: also treat 75 % of the scale maximum as meeting (7.5 / 10 would meet).
Source: "cumulative undergraduate grade point average (CGPA) of 75% or 3.00 GPA on a 4 point scale".
Recommend: **accept without the option**; the page does not say how other scales map.

**D09 · GRE or GATE result, any score,** unless the degree is from the EHEA,
Switzerland or the UK. With no minimum, "has a result" is checked as any GRE
Quantitative score (130 is the lowest possible) or any GATE scorecard. A student
with no test sees "missing information", not "still needed". Russia and Belarus
(uncertain EHEA status) stay unknown, never exempt. A degree from a branch
campus outside the EHEA is shown as a note.
Source: "required to upload the test result from the GRE General Test or the Indian GATE test" / "There is no minimum score requirement".
Recommend: accept.

**D10 · English, closed list.** It accepts IELTS 7.0, TOEFL iBT 95, TOEFL paper
600, CAE or CPE grade A-C, or PTE 76. Expired and home-edition tests count;
university or medium-of-instruction letters do not. Native speakers from
AU/IE/CA/NZ/UK/US, people who studied there in person, and German Abitur holders
are "Saarland decides". Citizenship only opens that review; it never exempts.
Source: "A confirmation of your university or a MOI (Medium of Instruction) is not a sufficient equivalent."
Recommend: accept.

**D11 · Subject content** (maths, theoretical and practical informatics; for
DSAI also ML/AI): "Saarland decides", since no credit numbers are published.
The DSAI sentence is quoted from the cached guide page. Recommend: accept.

### TU Darmstadt (Computer Science, AI and Machine Learning)

Both programmes get the same six rules.

**D12 · 60 ECTS matching the core courses of the TU Darmstadt B.Sc.** The
student enters their own count (partial overlaps counted proportionally, so
59.5 fails). A separate hard rule says TU Darmstadt makes the official
content check.
Source: "Minimum 60 ECTS must match the core courses of our B.Sc. Informatik in content, academic level, and depth".
Recommend: accept.

**D13 · Entrance exam.** It is needed only when the documents cannot confirm the
competencies. A GRE with Verbal 155, Quantitative 165 and Writing 3.5 (all
three) exempts. Otherwise "TU Darmstadt decides" (invitation and exam result),
never "does not meet". The GATE route (overall 750) is in the note: the profile
has no GATE score.
Source: "Verbal Reasoning ≥ 155 Quantitative Reasoning ≥ 165 Analytical Writing ≥ 3.5".
Recommend: accept, keep it hard (it can block admission).

**D14 · English, closed list:** IELTS 7.0, TOEFL iBT 95, or official
confirmation that the whole bachelor's was taught in English. A student with
only Cambridge CAE sees "does not meet". The programme pages say "English C1",
but the admission guide lists only these.
Source: "IELTS overall ≥ 7.0 or TOEFL iBT ≥ 95" / "Or an official confirmation that English was the language of instruction for your entire Bachelor's programme".
Recommend: accept (the guide is the specific source).

### TUM Data Engineering and Analytics

**D15 · Same structure as the accepted TUM Informatics rules** (degree, GRE or
GATE for degrees from Bangladesh, China, India, Iran or Pakistan, English list,
aptitude assessment, APS, VPD). There are two differences:
- Only the GATE CS paper counts. The Mechanical Engineering paper is accepted
  only "for M.Sc. CSE", a different programme.
- The English "TUM decides" note also names English-taught credits and an
  English bachelor's thesis, from the same language page.

The English quotes come from the cached language page, whose English section
the cleaned text lost (the known parser bug, fixed in Phase 5). The aptitude
assessment names both an interview and a written test, as the two pages differ.
Recommend: accept.

### KIT Computational and Data Science

**D16 · Credit areas.** It needs basic maths 20, a thesis (or similar
independent work) 6, and 40 credits in one of three areas plus 12 in each of
the other two. The three areas are (1) applied maths / maths for CDS,
(2) computer science, (3) natural sciences, engineering or economics.
Source: "Mindestens 40 LP aus einem und mindestens 12 LP aus den beiden verbleibenden Gebieten".
Recommend: accept.

**D17 · Conditional admission when up to 12 credits are missing.** The engine
cannot add up a total shortfall, so it uses two cut-offs derived from the 12:
basic maths at least 8 and one area at least 28. Below either, the student is
more than 12 short, so the result is "does not meet". Between those cut-offs and
the full minimums, "KIT decides" (admission on conditions is discretionary).
Neither 8 nor 28 is published; both follow from the 12.
Option: drop the cut-offs, so any shortfall is "KIT decides".
Source: "Fehlen Mindestleistungen im Umfang von bis zu 12 LP, kann die Zugangskommission eine Zulassung unter Vorbehalt aussprechen."
Recommend: **accept the cut-offs**.

**D18 · Whether one course may count twice, and which area a module belongs
to:** a hard "KIT decides" rule. The page is silent. Recommend: accept.

**D19 · English, same shape as KIT CS,** kept as an admission rule. It accepts
an entirely English-taught degree, TOEFL 90, IELTS 6.5 (no section below 5.5),
TOEIC, PTE 58.5 with section minimums, or Cambridge. School-certificate and
UNIcert routes are "KIT decides". The record omits the education routes; they
are quoted from the cached page. Recommend: accept.

### TU Berlin (Computer Science)

**D20 · Credit areas, each its own number.** It needs foundations 36 in total
(entered as its own figure, so nothing is added up twice): theoretical CS 12,
computer engineering / IT 12, methodological and practical CS 12. It also needs
mathematics 18 and 30 further CS credits without the thesis, on top of those.
Source: "36 CP in foundations of computer sciences, including 12 CP in the field of Theoretical Computer Science".
Recommend: accept.

**D21 · Module allocation is a hard "TU Berlin decides" rule.** It includes the
published exclusions: discrete structures and maths, algorithms, data structures
and digital logic do not count as theoretical CS. Recommend: accept.

**D22 · English.** It accepts IELTS 6.5 (5.5 is not enough even though it
certifies B2), or a completed degree from one of the 20 countries on TU Berlin's
native-English list. Other certificates on the faculty list are "TU Berlin
decides".
Source: "an overall band score of 6.5 is required, even if an overall band score of 5.5 confirms a B2 on the certificate".
Recommend: accept.

**D23 · To-dos.** A VPD is needed for every foreign degree; the "from summer
2026" date has passed. The Suitability Assessment Form is shown to everyone,
because the profile cannot say "my bachelor's is from TU Berlin" (those
students are exempt). Recommend: accept.

### TU Dresden (Computer Science)

**D24 · English.** It accepts IELTS 7.0, TOEFL iBT 95 or new-scale 5.0 (the
record omits the 5.0; the page has it). Other C1 tests are "TU Dresden decides".
Source: "TOEFL iBt (120-95) (New: 5.0 points) or the IELTS test was passed with at least level 7.0".
Recommend: accept.

**D25 · APS for "Chinese, Vietnamese or Indian educational certificates",** read
as the degree country, the same as TUM and Saarland. Option: also school
country. Recommend: **accept (degree country)**.

### University of Stuttgart (Computer Science)

**D26 · English, closed list.** It accepts TOEFL 95 or new-scale 5, IELTS
Academic 7.0, PTE 76, CAE or CPE (grade A-C; the page gives no grade, so this
uses the Cambridge convention), Oxford Test of English Advanced at C1 or C2,
telc C1/C2, or telc University with "very good". Medium of instruction is
expressly not accepted. Native-English citizenship opens only a "Stuttgart
decides" review, because education there is also required.
Source: "Accepted proofs are: TOEFL IBT 95 points / from 2026: 5 or better / IELTS band 7.0 or better (academic)".
Option: replace the Oxford and telc tests with one "Stuttgart decides" line
(fewer test names, but English could then never fail).
Recommend: **accept as written**.

## 3. Mechanical copies and conventions already decided (skim)

Numbers and lists copied as published, or conventions applied as decided
earlier. Correct one only if a number is wrong.

| Programme | Copied |
|---|---|
| All 11 | Degree subject / equivalence = hard "university decides" |
| All with a published selection or aptitude step (Saarland, TUM DEA, TU Dresden, Stuttgart) | Selection = hard "university decides" |
| RWTH CS, DS | GRE QR > 75th pct, VR > 15th pct, AW ≥ 3.5 |
| Saarland CS, DSAI | Top 10 % of class (10 counts); APS for degrees from China, India, Vietnam (to-do) |
| TU Darmstadt CS, AIML | 180 ECTS; 60 core-course ECTS |
| TUM DEA | GRE QR 164 + AW 4.0 or qualifying GATE CS, for Bangladesh/China/India/Iran/Pakistan degrees; IELTS 6.5, TOEFL 88, PTE 65, CAE/CPE A-C, ≥ 50 % English instruction; APS (China/India/Vietnam), VPD (to-dos) |
| KIT CDS | 180 ECTS; credit minimums 20 / 6 / 40 / 12 / 12 |
| TU Berlin CS | 36 / 12 / 12 / 12 / 18 / 30 credits |
| TU Dresden CS | APS (China/Vietnam/India, to-do) |
| Stuttgart CS | Certificate validity to the deadline = hard "university decides" (no date check yet) |

Not written on purpose: deadlines and fees (need the date engine), and
requirements the record marks "not published" (for example APS at KIT CDS,
TU Berlin and Stuttgart). "Not published" is never read as "exempt".

## 4. Engine gaps (what the student sees meanwhile)

| Gap | Programmes | What the student sees now |
|---|---|---|
| No "university confirmed my degree" fact (X1) | all 13 | Never a positive verdict |
| No dates: test age, certificate validity, deadlines (partly closed on branch date-logic-deadline-readiness, PR #9: `deadline` and `max_age` checks; KIT deadlines encoded, pending; test age still a review note) | KIT, Stuttgart, all deadlines | "University decides" note; no deadline check |
| No GATE score (only "qualified") | TU Darmstadt (GATE 750) | GATE route is "university decides" |
| No "I have no GRE/GATE" answer for tests without a minimum (closed on branch profile-explicit-no-gre-gate, PR #7, 2026-11-04: `gre`/`gate` accept "none") | Saarland | "Missing information" instead of "still needed" |
| No generic English CEFR level, school English certificate or UNIcert for KIT | TU Berlin, Dresden, KIT, RWTH | Those routes are "university decides" |
| No module-content or module-allocation facts | RWTH DS, TU Berlin, KIT CDS, Darmstadt | "University decides" |
| No total-shortfall arithmetic | KIT CDS | Cut-offs from D17 |
| No "bachelor's from this university" fact | TU Berlin | Suitability form shown to everyone |
| IELTS Academic vs General not recorded | RWTH DS, Saarland, TUM, Stuttgart | Any IELTS score is read as Academic |
| No exam-result fact | TU Darmstadt | Entrance exam stays "university decides" |

## 5. Names the future profile form must use

- Credit areas (`subject_credits`): `core_courses` (TU Darmstadt);
  `basic_mathematics`, `bachelor_thesis`, `applied_mathematics`,
  `computer_science`, `science_engineering_economics` (KIT CDS);
  `foundations_total`, `additional_cs` (TU Berlin). Reused: `theoretical_cs`,
  `computer_engineering`, `practical_cs`, `mathematics`.
- Language tests: `TOEFL PBT`, `UNIcert` (II-IV), `TOEFL iBT (2026 scale)`,
  `Oxford Test of English Advanced`, `telc`, `telc University`, plus the
  existing IELTS, TOEFL iBT, PTE Academic, TOEIC, FCE, CAE, CPE.
- Documents: `suitability_assessment_form`, plus `aps_certificate` and `vpd`.
- Countries: English short names ("United Kingdom", "United States").
