You are reviewing two skill instruction files that were flagged as possibly containing conflicting instructions. Identify the specific conflicts between them. The higher-level skill has priority (hierarchy: enterprise > team > personal).

Two instructions conflict only when a reader could not follow both at once, for example:
- one requires something the other forbids;
- they prescribe incompatible values, formats, tools or steps for the same situation;
- they give opposite rules for the same trigger or condition.

These are NOT conflicts:
- the skills cover different topics or situations;
- one adds rules or detail the other does not mention;
- the skills overlap but their instructions are compatible;
- one rule is stricter than the other but following the stricter rule also satisfies the looser one;
- they differ only in wording, tone, structure, name or description.

Compare the frontmatter metadata and instructions in the body of each skill.

List every conflict you find, numbered 1, 2, 3 and so on, in plain text with no headings or other markdown. Write each conflict in at most three sentences: the topic, what the higher-level skill instructs, what the lower-level skill instructs (quote or closely paraphrase the instructions), and why both cannot be followed. List only real conflicts as defined above; do not add weak or doubtful ones to make the list longer. If you find no real conflict, reply only with: No clear conflict found.

<higher_level_skill level="{higher_level}" name="{higher_label}">
{higher_text}
</higher_level_skill>

<lower_level_skill level="{lower_level}" name="{lower_label}">
{lower_text}
</lower_level_skill>