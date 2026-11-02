# Country groups and Cambridge grades: review sheet

Fetched 2026-10-29. Nothing here is built yet. You answer the yes/no items at the bottom; I build only what you accept. No code or JSON to read.

## Answers recorded 2026-10-29
1 yes (lists as shown). 2 yes (re-check notice after 12 months). 3 yes: Russia and Belarus are exempt at KIT through Lisbon and "university decides" for EHEA-only rules. 4 yes: the United States is "university decides" at KIT. 5 not on a list means the exemption does not apply, so the test is needed; refine later. 6 yes (fixed names, aliases). 7 keep the Cambridge guard. 8 EEA and RWTH Data Science left out for now.

Built: `data/eligibility/country_groups.json`, `eligibility/groups.py`, `@EHEA`-style values in rules, and the KIT GRE rule now depends on the degree country.

## Why this exists
Four programmes say "GRE/GATE required unless your degree is from ...": KIT CS, Saarland CS, Saarland DSAI (all three use EHEA; KIT also uses the Lisbon Convention) and RWTH CS (EU). The engine cannot answer "do I need the GRE?" without those country lists. Anything not on a list counts as "not exempt", so the student is told the test is needed (the safe direction).

## The three lists (open the source to check them)

**EHEA, 49 countries.** Source: https://ehea.info/about-ehea/bfug-members/ ("49 countries and the European Commission").
Albania, Andorra, Armenia, Austria, Azerbaijan, Belarus (suspended), Belgium, Bosnia and Herzegovina, Bulgaria, Croatia, Cyprus, Czech Republic, Denmark, Estonia, Finland, France, Georgia, Germany, Greece, Holy See, Hungary, Iceland, Ireland, Italy, Kazakhstan, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Moldova, Montenegro, North Macedonia, Norway, Poland, Portugal, Romania, Russian Federation (suspended), San Marino, Serbia, Slovak Republic, Slovenia, Spain, Sweden, Switzerland, Netherlands, Türkiye, Ukraine, United Kingdom.
The page says Russia's and Belarus's rights of representation are suspended since 2022; they are still listed.

**Lisbon Recognition Convention, 57 ratifying states.** Source: https://www.coe.int/en/web/conventions/full-list?module=signatures-by-treaty&treatynum=165 (status as of 29/10/2026).
Albania, Andorra, Armenia, Australia, Austria, Azerbaijan, Belarus, Belgium, Bosnia and Herzegovina, Bulgaria, Canada, Croatia, Cyprus, Czech Republic, Denmark, Estonia, Finland, France, Georgia, Germany, Greece, Holy See, Hungary, Iceland, Ireland, Israel, Italy, Kazakhstan, Kyrgyzstan, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Moldova, Monaco, Montenegro, Netherlands, New Zealand, North Macedonia, Norway, Poland, Portugal, Romania, Russian Federation, San Marino, Serbia, Slovak Republic, Slovenia, Spain, Sweden, Switzerland, Tajikistan, Turkmenistan, Türkiye, Ukraine, United Kingdom.
The United States **signed in 1997 but never ratified**. KIT's page says "signatory state", which could include it.

**European Union, 27 countries.** Source: https://european-union.europa.eu/principles-countries-history/eu-countries_en ("Pages (27)"; the page lists Austria to Netherlands, and Poland, Portugal, Romania, Slovakia, Slovenia, Spain, Sweden are on its second page, which I did not open).
Austria, Belgium, Bulgaria, Croatia, Cyprus, Czechia, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta, Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia, Spain, Sweden.
EEA (needed only for RWTH Data Science, which goes by citizenship) is these 27 plus Iceland, Liechtenstein and Norway. I have not fetched an EEA source, so I would not build it yet.

## What each programme does with them
| Programme | Exempt from GRE/GATE if the degree is from |
|---|---|
| KIT CS | an EHEA country, or a Lisbon Convention state, or the student has a successful GATE |
| Saarland CS and DSAI | the EHEA, Switzerland or the UK |
| RWTH CS | the EU (the page says "first degree is from outside the European Union" needs GRE) |
| RWTH DS | not the degree country: EU/EEA **citizenship** or German schooling (not built yet) |
| TUM | no groups: a fixed list of 5 countries needs it |

## Examples you can check by hand against the lists
| Degree country | KIT CS | Saarland | RWTH CS |
|---|---|---|---|
| India, China, Pakistan, Bangladesh, Iran | test needed | test needed | test needed |
| Germany, France | exempt | exempt | exempt |
| Türkiye | exempt | exempt | test needed |
| Switzerland, Norway | exempt | exempt | test needed |
| Canada, Australia | exempt (Lisbon) | test needed | test needed |
| Russia, Belarus | exempt (Lisbon) | **university decides** (EHEA-suspended) | test needed |
| United States | **university decides** (signed, not ratified) | test needed | test needed |

## Cambridge grade cards (what "grade" means)
Cambridge sends a Statement of Results with a **grade and a score on the Cambridge English Scale**. Sources: [Scale factsheet](https://www.cambridgeenglish.org/images/167506-cambridge-english-scale-factsheet.pdf), [C1 Advanced results factsheet](https://www.cambridgeenglish.org/images/664448-c1-statement-of-results-factsheet.pdf), [results page](https://www.cambridgeenglish.org/exams-and-tests/qualifications/results/).
- **C1 Advanced (CAE):** grade A = 200 to 210 (shown as Level C2); grade B or C = 180 to 199 (Level C1). A score of 160 to 179 gets a certificate "at Level B2" and **no grade**.
- **C2 Proficiency (CPE):** a score of 180 to 199 gets a certificate at Level C1 and no grade; grades A to C are above that.
- **B2 First (FCE):** grade A = 180 to 190 (shown as C1), grade B = 173 to 179 (B2); grade C and then a Level B1 certificate below.
KIT's page lists the three certificates and **publishes no minimum grade or score**; two other KIT pages say "CAE or CPE" without a grade either. My guard "grade A, B, C or pass" therefore means: the student passed at the exam's own level, and a "Level B2" CAE result does not count as C1. If you drop the guard, a Level B2 result would also count.

## Your answers (reply with the number and yes/no)
1. **Lists:** build the EHEA, Lisbon and EU lists above as they are, each marked with its source and date 2026-10-29?
2. **Lists change:** mark them "re-check after 12 months", so the report says so when older?
3. **Suspended members:** Russia and Belarus show as "university decides" for EHEA-based rules (Saarland), but exempt for KIT through Lisbon?
4. **United States and Lisbon:** "university decides" for KIT (signed, not ratified)?
5. **Not on a list:** counts as "test needed" (safe direction)?
6. **Country names:** the form will offer fixed names (Czechia/Czech Republic, Türkiye/Turkey and Russia/Russian Federation are treated as the same country)?
7. **Cambridge:** keep the guard (pass at the exam's own level, A to C) or drop it?
8. **EEA and RWTH DS:** leave out for now (needs its own source and the citizenship rule)?
