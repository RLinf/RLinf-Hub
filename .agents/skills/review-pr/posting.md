# Posting a GitHub review

Read this file only when the user asks to post, update, or reply to a review on GitHub.

## 1. Build, lint, and post

Write the GitHub create-review API payload as JSON in a temp file (`json.dump` for clean escaping), lint it, then post it. `body` is the main comment from `review-pr/SKILL.md` step 8 (without `### Inline comments` or `## Check summary`):

```bash
python3 .agents/skills/review-pr/lint_review.py template      # main-comment skeleton
python3 .agents/skills/review-pr/lint_review.py lint --pr "$N" review.json
python3 .agents/skills/review-pr/lint_review.py post --pr "$N" review.json
python3 .agents/skills/review-pr/lint_review.py update --pr "$N" --review <id> review.json
```

```json
{
  "commit_id": "<PR head SHA>",
  "event": "COMMENT",
  "body": "<the main comment>",
  "comments": [
    {"path": "models/foo/foo/adapter.py", "line": 42, "body": "<inline comment>"},
    {"path": "models/foo/configs/foo.yaml", "start_line": 10, "line": 12, "body": "<inline comment>"}
  ]
}
```

- `event` is `COMMENT`, or `REQUEST_CHANGES` when asked (`APPROVE` only when explicitly asked).
- `post` runs `lint`, posts everything as one review, and prints its URL. Report the URL and inline comment count to the user.
- Update a posted review in place (`lint_review.py update` for the body; edit or reply on inline threads). Only a new review round on a new head posts a new review. If `post` fails without printing a URL, check `gh api "repos/RLinf/RLinf-Hub/pulls/$N/reviews"` before retrying.

## 2. Where each finding goes

- **Inline (`comments[]`)**: any finding anchored to a diff line (or block `start_line`..`line`). Use `"side": "LEFT"` only for a deleted line that should stay. For a docs-style rule repeated on many lines of one page (such as CJK hard-wrapping), comment on the first line and note the remaining lines rather than opening a thread per line.
- **Main comment (`here`)**: findings with no single diff line (missing file, missing catalog row, missing tests, PR metadata).
- **Existing threads (`thread`)**: on a re-review, reply on the open thread instead of opening a duplicate thread on the same line, and mark that row `Posted = thread` in the Findings table:

```bash
gh api "repos/RLinf/RLinf-Hub/pulls/$N/comments/<id>/replies" -f body="..."
```

## 3. Writing inline comments

Each inline comment is self-contained (not repeated in the main comment) and has four parts:

1. **Header**: `**F<n> · <severity> · <category>: <plain title>**` matching its row in the Findings table.
2. **Problem (1–3 sentences)**: what the code or doc tries to do, what happens instead, and why it matters.
3. **`Suggested fix:`**: one direct sentence stating what to change, followed by a verified `suggestion` block (when replacing the commented lines) or a fenced code block.
4. **`Evidence:`**: one short line with the command/check result or trace (for unresolved findings, what settles it).

Keep prose plain and direct: short sentences, active voice, one line per paragraph, no HTML, no hedging, no filler. Write in English unless asked otherwise.
