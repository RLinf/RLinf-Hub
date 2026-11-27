# Writing English

An English README or PR comment should read as if an engineer who writes English natively explained the component to a colleague: direct, concrete, and concise. These rules apply to all RLinf-Hub Markdown docs, PR descriptions, review comments, and commit messages.

## Voice

- Write in plain, readable English that a colleague understands on the first read. Prefer concrete verbs over abstract jargon or stiff spec-sheet wording.
- Address the reader as "you" and give instructions in the imperative ("Export `RLINF_EXT_MODULE`", "Run the smoke test").
- Write in the present tense and active voice ("The adapter maps observations", not "Observations are mapped").
- Lead with the outcome: say what the reader gets or does, then how.
- Write "Use X" instead of "Consider using X" or "You may want to use X"; reserve "may" and "might" for genuine uncertainty.
- Keep paragraphs short (1–3 sentences) and put each paragraph on one line in Markdown source.

## Words to cut

| Cut | Why | Write instead |
|---|---|---|
| simply, just, easily, obviously, basically, of course | the step may not be simple for the reader | nothing |
| seamlessly, powerful, robust, comprehensive, cutting-edge, state-of-the-art, leverage, crucial, pivotal, delve, showcase, unlock, empower | sales or machine register | the concrete fact, or nothing |
| it is worth noting that, note that, please note, importantly | filler | the fact itself, or a callout |
| in order to, allows you to, enables you to, is able to | wordy | to, you can, can |
| currently, new, now, no longer, recently | goes stale | the version or scope, or nothing |
| a wide range of, various, a variety of | vague | the actual items or count |

## Constructions to avoid

- Negative-contrast framing ("this is not A, not B, but C", "not just X, but Y", "X rather than Y" used as padding). State directly what it is unless clearing up a real misconception.
- Trailing "-ing" benefit clauses ("…, ensuring reliable inference"). State the concrete consequence or cut it.
- Announcements instead of content ("In this section, we will…", "As mentioned above", "Let's take a look at…").
- Rotating synonyms for one thing (env, environment, simulator, task); pick one term and keep it consistent.

## Calques from Chinese

| Avoid | Write |
|---|---|
| video memory | GPU memory |
| realize support, realize the function | support, implement |
| carry out training, perform the training | train |
| open or close the switch | enable or disable |
| in the case of | if, for |
| based on (for 基于, everywhere) | with, using, on, or restructure |
| it is necessary to | you must, or use the imperative |

## Headings

- Keep headings short and scannable (`Install`, `Register with RLinf`, `Run Evaluation`, `Verification`).
- Avoid code identifiers as standalone headings unless documenting a reference table.
