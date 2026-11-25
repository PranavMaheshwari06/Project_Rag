# Privacy notice

This project is not deployed yet. This notice says what the software does with what you send it. Before a public
instance goes online it will also state where that instance is hosted, what the host logs, and which tier of the
language-model provider it uses.

**Do not type personal details** (your name, passport or application numbers, contact details) into a question, a
pasted text or a feedback note. Nothing here needs them. The service is for adults (18 or older), which is also a
condition of the model provider.

## No accounts, no cookies

There is no sign-up. The app sets no cookies, stores nothing in your browser and loads no analytics.

## What leaves the server

Written answers come from Google's Gemini API when the server is set up with a key. Without a key, answers are
quoted on the server from the official pages (and from your pasted text, if you sent one), and nothing is sent to a
model.

| what you send | what goes to the model provider |
|---|---|
| a question | the question and the retrieved passages of official pages |
| a pasted text with a question | the question, the passages and your pasted text |
| a pasted description of yourself, to draft a profile | that text, whole |
| a profile, in the chat | your question and the rules engine's result for each requirement (for example "English: does not meet", with the requirement and the next step). Not the values you entered, although these results say something about you |
| a profile, in the eligibility check | nothing: a rules engine on the server computes it |

What the provider does with it depends on the tier of its API
([Gemini API terms](https://ai.google.dev/gemini-api/terms), as effective on 23 March 2026; they can change):

- **Paid tier:** Google does not use prompts or answers to improve its products. It logs them for a limited time to
  detect breaches of its use policy and to meet legal duties, and may store them in any country where it operates.
- **Free tier:** Google uses prompts and answers to improve its products and human reviewers may read them. Google
  asks that no personal or sensitive information is sent. Its terms treat users in the European Economic Area,
  Switzerland and the United Kingdom differently, and allow only the paid tier in an app offered to them.

## What the server keeps

- **Logs:** one line per request with the time, a request id, the page asked for, the status, how long it took, how
  many model calls and tokens it used, and the length of what you sent. These lines hold no question, pasted text,
  profile, feedback note or network address. An unexpected crash writes an error report that could quote part of an
  input. A hosting company can keep logs of its own.
- **Request limits:** a scrambled (salted hash) form of your network address, in memory only, to stop abuse. It is
  never written down, and a restart erases it.
- **Answer cache:** an answer to a question without a profile or pasted text can be reused for the same question for
  up to 24 hours. It is held in memory only. The answer may repeat words from the question.
- **Profiles and pasted texts:** used for that one request and not stored.
- **Feedback:** only when you send it and agree to it being stored: the time, the id of the answer, optionally the id
  of an official page, and your note (up to 500 characters). It is kept for 90 days and removed at the first restart
  or new note after that.

## Having a note deleted

Open an issue in the project's
[GitHub repository](https://github.com/PranavMaheshwari06/Project_Rag/issues) with the answer's request id (the
`x-request-id` of that answer). Issues are public: quote the id only, not your note.
