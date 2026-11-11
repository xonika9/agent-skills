---
name: x9-better-questions
description: Use whenever the user shares notes or a transcript of a talk with a customer, user, or potential client, drafts questions for such talks, starts or sums up a series of customer interviews (custdev), or wants to rehearse one with you playing the customer — the method of Rob Fitzpatrick's The Mom Test («Спроси маму») for getting facts instead of polite approval, for example «разбери разговор с клиентом», «вот заметки после встречи», «проверь мои вопросы», «начинаю серию интервью», «потренируй меня перед кастдевом», "prepare customer interview questions". Do not use for surveys or questionnaires, usability tests of a prototype, criticizing an idea without customer conversations (x9-idea-critic), or job interviews.
---

# Better questions

People are kind: asked about your idea or about their future, they say what you hope to hear. This skill keeps customer conversations on what the other person has actually done, so the answers can change a decision. The method comes from Rob Fitzpatrick's *The Mom Test*; [the method reference](references/method.md) restates it and is read before producing any output below. Output shapes live in [templates](references/templates.md).

## A test for every question

Beyond the three rules in the method reference, ask of every question you write, review, or hear asked: could the person answer pleasantly whether or not the idea is any good? Then the answer carries no information; rewrite toward a specific past event.

## Choose the mode from what the user brings

| The user brings | Mode |
|---|---|
| An idea, problem, or segment, and wants to get ready | Prepare |
| A draft list of questions | Review |
| Notes or a transcript of one conversation | Debrief |
| Several debriefs, or asks "what now?" after a series | Synthesis |
| A wish to rehearse | Practice |

Ask one question only when the input fits two modes and the choice changes the output.

**Prepare.** Narrow the segment until the user can name where to find these people; push back on segments like "small business". Name the three riskiest assumptions, including one the user is afraid to hear answered. Write 5–8 questions, each tied to one of those risks; a question that informs none is cut. Confirm that the problem matters before asking about its details, and send anything a web search can answer to desk research instead. Plan three levels of ask for the end of the conversation. Deliver the plan and the one-page cheat sheet; add an outreach message when the user needs to arrange meetings.

**Review.** Judge every question. Keep the good ones, and for each failing one say what makes it fail and give a rewrite plus a follow-up; never drop a question without a replacement or the reason it informs no decision.

**Debrief.** Sort everything in the notes into facts, signals, material that is not evidence, and commitments. A friendly deferral such as «держите в курсе» is a polite no, not a commitment. Coach the interviewer on where they pitched, fished for approval, or let vague claims pass. End with what changed for each risk and what to ask next time.

**Synthesis.** For each risk, conclude confirmed, refuted, or unknown, citing the conversations behind it. Give one verdict: continue, narrow or change the segment, or stop. Lukewarm interest is evidence for stopping, not for continuing; answers that contradict each other point to a segment that is too broad. Say whether more conversations would still teach anything.

**Practice.** Build a specific person from the target segment and decide privately, before the first line, how much the problem really matters to them; keep that hidden truth consistent. Play them as polite and agreeable: pitches get compliments, vague questions get vague answers, and facts come only in response to good questions. Stay in character until the user stops or about ten exchanges pass, then step out and review the rehearsal in words, without points or grades: quote the questions that failed, the bad data accepted at face value, the signals not followed up, and whether an ask was made. Finish with the two or three changes for the real conversation.

## Research folder

When the user starts a series of conversations, ask once where to keep it before creating anything, even when they ask you to set it up, proposing `./research-<topic>/` in the current working folder; storage rules of the workspace, such as its `AGENTS.md`, take precedence over that proposal. Keep `plan.md`, one file per conversation in `interviews/` named by number, person, and date, and `synthesis.md`. Read the existing folder before writing to it and update files in place so the user's own edits survive. Without a series, everything stays in the chat.

## Rules for every mode

- Write questions and results in the user's language, phrased the way a person would actually say them.
- Evidence is only what the user's material contains. When something needed is missing, say so instead of filling it in; never invent quotes, numbers, or outcomes, and label assumptions as assumptions.
- State verdicts plainly. The decision about the idea stays with the user.

## Done

The mode's template in [templates](references/templates.md) is filled from the user's material, with every gap marked as missing rather than guessed, and in a series it is saved to the matching file in the research folder; in Practice, the review quotes the user's own questions.
