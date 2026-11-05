You are reviewing two skill instruction files, a higher-level skill and a lower-level skill, to find out whether their instructions contradict each other.

Two instructions conflict only when a reader could not follow both at once, for example:
- one requires something the other forbids;
- they prescribe incompatible values, formats, tools or steps for the same situation;
- they give opposite rules for the same trigger or condition.

These are NOT conflicts:
- the skills cover different topics or situations;
- one adds rules or detail the other does not mention;
- the skills overlap but their instructions are compatible;
- one rule is stricter than the other but following the stricter rule also satisfies the looser one (for example, "max 72 characters" and "max 50 characters");
- they differ only in wording, tone, structure, name or description.

Compare the frontmatter metadata and instructions in the body of each skill.

<higher_level_skill level="{higher_level}" name="{higher_label}">
{higher_text}
</higher_level_skill>

<lower_level_skill level="{lower_level}" name="{lower_label}">
{lower_text}
</lower_level_skill>
