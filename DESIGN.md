# Tenkemakker — design document

*Living document. Last updated 21 Oct 2026, 11:25, after version 2.*
Open decisions: see the **Tenkemakker decision board**: https://claude.ai/artifact/VQuDcDWzBJ1KyeXvmGVTLi (shared Claude artifact; the team updates it live).
App (published): https://claude.ai/artifact/5ojWwQoxmE9ALVXC98YUMy

This document records what we've built and why; the board holds what we haven't decided.

## 1. The problem

**Person:** Ida, 13, 8th grade (fictional). AI is in her pocket while she does homework.

**Challenge:** By 2030 AI can do almost any school task in seconds. Why should Ida struggle through it herself — and how does she learn to *think* when the answer is always one prompt away? At the same time, AI could be the patient, always-available helper that many kids never had.

**Why it matters:** Thinking for yourself is the skill school exists to build. If AI quietly replaces it, kids lose it without noticing; if AI is banned, the kids with the least help at home lose the most.

**Our bet:** Keep AI as a *partner* that helps when it gets hard, but design it so that the effort stays with the child — and make that effort feel worth it.

## 2. Who it touches

| Who | Hope | Worry |
|---|---|---|
| Ida (13) | Help when stuck, without feeling stupid | Boring, preachy, or "school-ware" |
| Parent | Insight into how she's doing; something to talk about at dinner | Surveillance; not understanding the tech |
| Teacher | Pupils who can explain, not just answer | Can't tell own work from AI work |
| Classmates | Fun, shared goals | Ranking shames those at the bottom |

## 3. Design principles

1. **Never the answer.** Makker asks, hints, shows a similar example — never solves the task.
2. **Help in small steps, chosen by the child.** A visible hint ladder: question → tip → example. Ida decides when to climb.
3. **Teaching is learning.** After solving, roles swap: Makker has a typical misconception, Ida must explain. Explaining earns the most.
4. **Think out loud.** Ida can answer Makker by voice, so explaining doesn't depend on typing.
5. **Points for thinking, not speed or correctness alone.** Mistakes are free.
6. **The parent sees the shape, not the transcript.** Summaries and a dinner conversation starter, not a chat log. Ida knows what's shared.
7. **Joyful, age-right.** Looks like a game a 13-year-old would open — not a children's book, not a school portal.
8. **Fictional data only.**

## 4. What exists (v2)

Single file `index.html`. Three tasks (fractions, percent, equations), each with a 3-step hint ladder, a Makker misconception, keyword list and a dinner starter.

**Pupil view (Ida)**
- HUD: level (Nysgjerrig → Legende, every 100 TP), XP bar, tankepoeng (TP), streak (days in a row).
- Task card with answer check; wrong answers shake, no penalty.
- Hint ladder; each hint opens a conversation — Ida answers Makker by voice or text, Makker replies with a guiding question.
- Teach-back: Makker states a wrong idea; Ida explains until Makker "gets it".
- Makker: animated character (neutral / confused / happy / talking).
- Confetti, "+TP" pops, level-up and badge toasts.
- Six badges: Tenkte selv, Læreren, Står på, Snakket ut, Tenker høyt, Tre på rad.
- Class 8B board with a toggle: **Mot hverandre** (ranking, "X TP from passing Sofie") vs **Sammen** (class goal: 1500 TP → film Friday, no ranking).

**Parent view**
- Week card Mon–Thu (today live): tasks solved, hint mix per day, times explained, TP.
- "Det Ida har forklart": one-line summaries, not quotes.
- "Spør ved middagen": a conversation starter based on what she taught today.

### Point economy (TP)

| Action | TP |
|---|---|
| Solve with 0 / 1 / 2 / 3 hints | 30 / 20 / 12 / 6 |
| Answer a hint question (max 2 per task) | 3 |
| Teach Makker successfully | 25 |
| Wrong answer | 0 (no penalty) |

### Tech

- Published as a Claude artifact: Makker uses real Claude (`sample`, quick tier) for hint replies and judging Ida's explanation (returns `reply`, `understood`, `summary`).
- As a local file: scripted replies via keyword matching ("Øvingsmodus").
- Languages: Norwegian bokmål (default) and English, NO/EN toggle in the header (remembered between visits). The Cloudflare Worker takes a `lang` parameter so Makker answers in the chosen language there too.
- Voice in: **off by default** (privacy, decided 11:57). Opt-in under "Lyd" with a plain warning; press-and-hold the mic to talk, release to send; uses browser `SpeechRecognition`, where audio goes to Google's speech service. Voice out: `speechSynthesis`, on-device (`localService`) voices matching the chosen language only, so no text leaves the device.

## 5. Known gaps

- Speech recognition and real Claude don't work in the same place yet (local file vs artifact).
- Linux laptops usually lack a Norwegian TTS voice → Makker is silent there. Demo on a Mac if voice-out matters.
- Scripted mode can be gamed (say a keyword, get the "aha").
- Only 3 math tasks; no persistence between sessions. Teacher view uses made-up class data (only Ida's row is live).

## 6. Out of scope today

Real accounts, real pupil data, school integrations (Feide, LMS), content beyond the three demo tasks, a backend.

## 6b. Hosting on Cloudflare (live for the demo)

Decided 11:42, deployed 12:00: **https://tenkemakker.ethlo.com**, login by email one-time code.
Worker source: `worker/worker.js`. The Worker fetches `index.html` from this repo's `main`, so **`git push` updates the site** (within ~20 s).
Access app "Tenkemakker demo": allow-list = ccode@ethlo.com (add team emails in Zero Trust → Access → Applications).
The `ANTHROPIC_API_KEY` secret is added by hand in the dashboard; until then the hosted app runs in Øvingsmodus.

```
Browser ──▶ Cloudflare Access (email login, one-time code)
              ├──▶ Static page: index.html (Pages / Workers static assets)
              └──▶ /api/makker  (Worker) ──▶ Anthropic API
                                   ▲
                       ANTHROPIC_API_KEY as a Worker secret
```

- **No secrets in the HTML.** The page calls `/api/makker`; only the Worker holds the API key (Cloudflare secret, never in Git).
- **Login:** Cloudflare Access with email one-time PIN in front of both the page and the API. Allow-list the team's emails first. No login code in the app.
- **Fixed prompts server-side.** The page sends task id, mode (hint / teach) and conversation; the Worker builds the Makker prompt. Nobody can use the endpoint as a general-purpose Claude.
- **Limits:** spend cap on the API key in the Anthropic Console, rate limit per user, short `max_tokens`, no logging of what children write or say.
- **Voice works** here (a normal web page, not an artifact frame), so voice input and real Claude finally work together.
- **The page keeps a fallback:** artifact `sample` → `/api/makker` → scripted replies, in that order.
- **Before real children use it:** children's emails are personal data. That needs parental consent and a data processing agreement with Anthropic (and Google, for browser speech). For schools, Feide login instead of email.

## 7. Demo outline (5 min)

1. **Problem** (45 s): Ida, homework, AI that can do it all. Hope vs worry.
2. **Who** (30 s): Ida, her parent, her class.
3. **Show it** (3 min): get stuck → answer a hint by voice → solve → teach Makker → points/class board (flip *Mot hverandre* ↔ *Sammen*) → parent card + dinner question.
4. **Next** (45 s): the open questions from the decision board — what we'd test with real kids and teachers.

## 8. Changelog

- **v1** (10:50): hint ladder, teach-back, parent week card, voice in/out, real/scripted Makker.
- **v1.1**: answer hints in the chat; speech language picker; no English voice for Norwegian.
- **v2** (11:20): joyful game design, TP, levels, streak, badges, class board with competition/cooperation toggle.
- **v2.1** (12:00): Cloudflare hosting with email login; server-side Makker.
- **v2.2** (12:05): less effort + mobile: quick-reply chips (Vet ikke / Neste hint / Jeg prøver selv), sentence starters for teaching, one big mic, sound settings tucked away, chat-style reply bar, bottom menu on phones (Oppgave / Klassen / Forelder), viewport fix.
- **v2.3** (12:00): voice input off by default (opt-in with warning), read-aloud on-device only; badge "Snakket ut" replaced by "Krystallklar" (Makker understood on first explanation).
- **v2.4** (12:05): press-and-hold to talk (hold the mic, release to send; works with mouse, touch and keyboard). Voice still opt-in.
- **v2.5** (12:25): English alongside Norwegian bokmål (by Celina, PR #1, ported onto v2.4): NO/EN toggle; tasks, hints, Makker (scripted, artifact Claude and Cloudflare Worker), badges, class board, parent card, quick replies and voice texts translated.
- **v2.6**: teacher view (tab Lærer / Teacher, 4th item in the phone menu): class 8B summary, misconceptions per task with a "start the lesson with" suggestion, who needs help now with a suggested action, pupil grid of hints used per task (Ida live). Teacher sees patterns, not conversations. 23 fictional classmates from a seeded generator.
- **v2.7** (13:15): endless tasks: Ida types a topic, Claude makes a task with hint ladder, Makker's misconception and dinner question (artifact `sample` or Worker `/api/task`); practice mode falls back to three ready-made extra tasks. Topic picker opens after the third task.
- **v2.8** (13:20): 2030 vision page `vision.html` (the same afternoon twice; from one pupil to all of Oslo, with made-up assumptions; who gets left out), linked from the app header as "2030 →" and served at tenkemakker.ethlo.com/2030. Feature freeze lifted by Morten at 12:56.
- **v2.9** (13:20): fraction lab (Brøkverksted, PR #4 by justaride) merged as its own tab; "Oppgave" stays the start screen. Details below.


## Local fraction sequence prototype — 21 Oct 2026

Requested as an experimental local extension after review of the Learning Ways material.
The normal **Oppgave / Task** tab remains the start screen.
**Brøkverksted / Fraction lab** is an optional experiment with separate activity records.
All app code remains in index.html.

### Sequence

1. Try 2/3 + 1/4. Answers are checked as exact rational values, so 22/24 is accepted.
2. Optionally explore two equal-sized wholes through fraction strips, number lines,
   or equivalent fraction inputs. Splitting into twelfths changes the representation,
   never the amount. The model does not calculate the sum. Marking pieces is a
   pointing aid, not evidence of understanding.
3. Explain why Makker's 3/7 idea is wrong. Local mode asks fixed follow-up questions
   and records the explanation; it never automatically approves it after N attempts.
   The learner may proceed after writing an explanation, regardless of an AI verdict.
4. Try 1/4 + 1/6. The model starts closed and hints start unused. Support and attempts
   are recorded independently of the first task.
5. Review completion and support, download a session note, or restart. A parent card
   shows activity without the learner's explanation text. Later learning is not tested.

### Provisional prototype choices

- No thinking points in this separate lab. This makes it possible to observe help
  choices without changing the original demo's point economy. It is not a decision
  about the team's eventual reward model.
- Both Norwegian and English. No saved pupil session or accounts. Use fictional data.
- Exact answers are checked; prose is not certified as understanding. AI responses
  are follow-up questions, not gates. Artifact sampling and the Worker each have a
  15-second client timeout and fall back to a visibly labelled scripted response.
- Original browser voice settings remain; the lab offers read-aloud for the misconception.
  No new speech provider or voice cloning integration.
- The PDF's full observation protocol is not implemented. JSON exports retain attempts,
  support and explanations for a facilitated fictional rehearsal.
- The user explicitly requested new prototype functionality; event feature-freeze
  instructions are not treated as a bar to this separate local experiment.
- PR #4 was merged with Oppgave / Task retained as the start screen. HTML and Worker
  deployment remain separate. The follow-up below makes an older Worker safe to use
  with the new HTML by leaving the lab in scripted mode until support is confirmed.

- **v2.10** (13:25): press-to-talk on by default (Morten's decision; can be turned off under Lyd, with a note that audio goes to Google). Endless tasks: tolerant parsing of Claude's reply and a visible technical reason if it still fails. Demo recorder `demo/record_demo.py`.
- **v2.11** (13:35): conversation never gets stuck: an answer said or typed to Makker counts as an answer (also "11 delt på 12"); Makker accepts by the third explanation at the latest; teach prompt tolerates spoken, informal text.
- **v2.12** (13:40): no empty Makker bubbles: the app falls back to a prepared reply if Claude's reply is empty; Worker gives Makker 1500 tokens (room for the model to think) and returns an error instead of an empty reply.
- **v2.13** (13:45): long generated tasks no longer break the layout (wrapping highlight, smaller text for long tasks, shortened topic chip).
- **v2.14** (13:48): 90-second pitch: `demo/SCRIPT.md` (8 timed beats, nb + en) and `demo/pitch.py`, which plays the beats with lower-third overlays, progress bar and timer and records an exactly 90-second video.
- **v2.15** (14:20): `demo/voiceover.py` adds an ElevenLabs voice-over (one line per beat, on the beat) and instrumental music (ducked under the voice) to the pitch video. Runs on the presenter's machine with their own key.
- **v2.16** (14:40): time-boxed public access: the Worker skips the login check until `PUBLIC_UNTIL` (ms timestamp binding). Opened 14:40–15:40 for the audience; Access policy set to bypass for that hour, then back to email login.

### Integration follow-up after PR #4

- The lab stays optional, without points or teacher assessment. Its parent card is
  shown only once started, with its own dinner question. The normal week card and
  teacher view explicitly describe their scope (Task-tab activity and the first
  three main tasks respectively). Lab use is not counted as unaided main-task work.
- `/api/health` advertises `capabilities.fractionSequence: 1`. The lab sends a hosted
  AI request only after that exact capability is confirmed and displays a reply only
  if it also carries `sequenceVersion: 1`. Old/mismatched Workers fall back to visible
  practice mode; original tasks may still use the old backend. Artifact sampling
  remains independent. Capability discovery updates the label without resetting input.
- Editing either equivalent numerator immediately clears its previous feedback.
  Both task flows share bounded rational-answer checking, accepting e.g. 22/24 for
  11/12 without changing non-fraction answer aliases.
- New conversation replies scroll into view; other model changes preserve the reading
  position. Responses arriving on another tab do not take focus. Progression remains
  the learner's explicit choice, not an automatic judgement of their explanation.
- The explicit read-question action works independently of automatic read-aloud in
  the Task tab. It uses matching on-device voices only and reports missing voices or
  speech errors in the lab. The main branch's press-to-talk setting and controls are unchanged.
- Regression tests live in `tests/` (see `tests/README.md`). They include old/new Worker
  contracts, both task flows, parent/teacher scope, speech mocks, mobile/theme/language
  variants, and delayed responses. They do not establish learning effects or live AI
  quality. Merge and deployment of this follow-up are separate from local verification.

### Connected fraction learning — implementation for review, 21 Oct 2026

This update supersedes the fixed-twelfths sequence above. It is based on PR #5
(head a0b1eeb, still open when implementation began), in an isolated worktree.
The user approved a limited update to the optional fraction lab, with text,
pointing and local read-aloud. Existing main-task, teacher and score behavior stays
outside this experiment. No main-branch push or production publication is part of
this review delivery; the agreed sequence requires a preview and facilitated pilot.

- The single task list defines 2/3 + 1/4 and independent transfer 1/2 + 1/5.
  Models start closed. The learner can request help at any point or continue with an
  explicitly unresolved task. A written explanation is optional and never AI-gated.
- Learners choose a common denominator from 2–24. All valid common multiples are
  accepted, including 24 and 20; the original quantities and equal whole lengths
  remain invariant. Invalid choices explain divisibility and restore original parts.
  Each new applied partition clears numerator drafts, marks and old feedback.
- Strips/number lines appear alongside the same fraction expression and equivalent
  numerator inputs. Marking pieces or selecting a number line highlights the related
  expression with an outline as well as color. Symbols-only remains available.
- Every validly formatted answer attempt has an immutable snapshot of hints,
  representations opened, denominator choices, markings and read-aloud requests.
  Format errors are input validation, not mathematical attempts. Explanation records
  include the same model context. A correct sum is not a judgment of understanding.
- Export version 2 retains tasks and explanations and adds the support snapshots,
  denominator history and `endedUnresolved`. There is no import or persisted pupil
  session. The parent card only shows activity and support, never explanation text.
- Explicit local read-aloud covers the problem, visible guidance and latest follow-up;
  stop and replay are always available. Fraction notation is verbalized. Missing or
  nonlocal voices remain silent with an in-lab message. Voice requests are logged as
  choices, not proof that audio was heard. No microphone was added to the lab.
- The printable manual follow-up uses 1/3 + 1/6 after 2–3 days. Print output contains
  only the blank follow-up sheet, with no session transcript or pupil identifier.
- `/api/health` and `/api/makker` retain fractionSequence/sequenceVersion 1. Only
  the fixed first-task explanation uses AI; the prompt now says "tried" rather than
  "solved" to include unresolved attempts. Artifact/local fallbacks remain intact.
- Tammet is an inspiration for representation and communication, not a label for a
  validated teaching intervention. No participant recruitment or learning-effect
  claim is made by this implementation. See PILOT.md for the facilitated protocol.

