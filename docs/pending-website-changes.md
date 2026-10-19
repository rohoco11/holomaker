# Pending changes: class-story.higgsfield.app (booklet website)

Status: **not applied yet**. The Higgsfield website checkout kept getting cut off at about 2 MB,
so these changes could not be made to the site repo. Apply them once `website_repo_access`
checkout works again.

- Higgsfield website id: `447af952-36ce-426b-8e55-9f5a85a6db39`
- Checkout path in the Higgsfield sandbox: `/home/user/website-19e36f870dd123e80c0eecb1`
- Site repo HEAD when last seen: `1d4e095 Student answers: minimum length 80 characters`
  (newer than my last commits; `88a7ac2` reworked image prompts, so read the current file before editing)

---

## Change 1: make the illustrated kids look 12–13, not about 9

**Request:** "for the image creation change the prompt slightly to make the kids look not so young.
currently the images make the kids look like 9 year olds. make the kids look a bit more mature but
still kids that are 12 to 13 year olds"

**File:** `app/src/lib/generation.server.ts`

Only booklets generated after the deploy are affected. Existing booklets (BLSF8M, S2TKYC) keep
their current images unless they are regenerated.

### 1a. `STYLE_RENDER_NOTES` (appended to every Higgsfield image prompt)

In **both** entries (`"동화책"` and `"다이어리"`), replace the phrase

> Depict a generic child (a boy or girl matching the student's gender given above; ...

with

> Depict a generic 12-13-year-old preteen (a Korean 6th grader about to finish elementary school;
> a boy or girl matching the student's gender given above; ...

and add this sentence right after that clause:

> Preteen proportions: taller and leaner than a young child, longer limbs, a less round face,
> a more grown-up and self-aware expression and posture -- but still clearly a kid, not a
> teenager or adult, and never a toddler or little-kid look.

Keep the existing "성별 미상" fallback (distant or back-turned figure) and the safety wording
unchanged: "Always generic: no specific likeness, no realistic face, never a real person."

### 1b. `"다이어리"` entry only

Replace

> a real child's build

with

> a real 12-13-year-old's build

The "NOT chibi, NOT a flat-design mascot" wording stays.

### 1c. `STORY_SYSTEM_PROMPT` (Claude writes the scene prompts)

Wherever the illustration rules tell Claude to use "a generic child" (the safety rule, the 동화책
rule "a generic child figure performing or symbolizing something concrete", and the 다이어리 rule
"a generic child living out the specific moment"), change it to
"a generic 12-13-year-old preteen". Keep "no specific likeness" / "no realistic face" exactly
as they are.

Also check the scene-prompt scrubber added in `88a7ac2`: if it rewrites or filters child wording,
make sure it doesn't strip the age phrase.

### Verify

1. `grep -n "generic child\|child's build" app/src/lib/generation.server.ts` should return nothing.
2. Reinstall deps (`npm i -g bun && bun install` in `app/`), then run `npx tsc --noEmit -p .`.
3. Commit, `website_repo_access` push, `deploy_website`, and poll `website_status` until it's live.
4. Optional: generate one test booklet and check that the kids read as 12–13.
