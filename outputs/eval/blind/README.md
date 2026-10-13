# Hand-scoring guide

Score a few of the B*.md briefs without opening key.json. Copy
human_scores_template.csv to human_scores.csv, fill in 1-5 per criterion for the
briefs you read, leave the rest empty, then run `uv run discovery-chef evaluate`.

## C1 Completeness
Does the brief answer all six questions: who the users are, which problems are real, what the evidence says, the competitors and market, the risks and open assumptions, and what to test next?

- 1: Several questions missing or answered in a line.
- 3: All questions present, some thin.
- 5: Every question answered with substance.

## C2 Evidence grounding
Are claims tied to specific sources, with the strength of the evidence made clear (how many usable interviews, behaviour versus stated preference, contradictions)?

- 1: Claims are mostly asserted; strength never discussed.
- 3: Claims are cited, but strength is stated only sometimes, or a citation misrepresents its source.
- 5: Every claim is cited, no citation misrepresents its source, and strength and caveats are explicit throughout.

## C3 Calibration
Does the confidence of each conclusion match the evidence, without overclaiming or burying real signals?

- 1: Overclaims (e.g. 'validated demand') or dismisses strong evidence.
- 3: Mostly calibrated, with a few overstatements or a confident claim resting on weak evidence.
- 5: Confidence matches the evidence in every section; uncertainty is explicit and nothing is overstated.

## C4 Actionability
Is the recommendation clear and justified, and are the next tests concrete (who, what, how many, success metric, the decision it informs) and prioritised by risk?

- 1: Vague recommendation; tests are generic ('do more research').
- 3: Clear recommendation; tests named but missing a sample, a success metric or the decision they inform.
- 5: Clear, justified recommendation; every test states who, how many, the success metric and the decision it informs, ordered by risk.

## C5 Clarity
Is the brief concise, well organised and easy for a product manager, designer and engineering lead to act on?

- 1: Hard to follow; padded or disorganised.
- 3: Readable, with some padding, repetition or citation clutter.
- 5: Tight, well structured and quick to act on; nothing could be cut.
