# data/

A place for your own skill files, so you can try SkillsCop against them.

## What goes here

SkillsCop reads skills from the folders you set in `settings.json`. This folder is a convenient, Git-ignored home for them. A typical layout:

```
data/
├── enterprise-skills/    # highest priority
├── team-skills/
├── personal-skills/      # lowest priority
└── skills-root/          # everything to compare for similarity
```

You can use any folders, inside or outside this repository. Just point the matching paths in `settings.json` at them:

| Setting | Used by | Purpose |
|---|---|---|
| `enterprise_skills_path` | `check-conflicts` | Enterprise level skills (highest priority) |
| `team_skills_path` | `check-conflicts` | Team level skills |
| `personal_skills_path` | `check-conflicts` | Personal level skills (lowest priority) |
| `skills_root_path` | `check-similarity` | Folder searched for similar skills |
| `reports_export_path` | both | Where CSV reports are written (created if missing) |

## File format

- Only `.md` and `.txt` files are read. Subfolders are searched too.
- For `check-similarity`, add a `description` to the YAML front matter of each skill. It is compared separately from the full text:

```markdown
---
name: example-skill
description: One sentence on what the skill does and when to use it.
---

The skill instructions go here.
```

## How the files are used

- **`check-similarity`** compares every pair of files under `skills_root_path` using TF-IDF cosine similarity, on both the full text and the description. Pairs above `file_cosine_similarity_threshold` or `description_cosine_similarity_threshold` are exported to a `similarity-*.csv` report.
- **`check-conflicts`** compares every skill at a higher level with every skill at a lower level (enterprise against team and personal, team against personal). A local model scores the chance that the lower skill contradicts the higher one. Pairs above `instructions_conflict_threshold` get a written explanation and are exported to a `conflicts-*.csv` report.

All models run locally through Ollama. Your skills are not sent to an external service.

## Good to know

- **Not tracked by Git.** Everything here except this README is listed in `.gitignore`, so your files are never pushed or overwritten by a pull.
- **Optional.** The app works with skills stored anywhere. Using this folder is only a convenience.
- **The paths must exist.** `validate-settings` checks that the enterprise, team, personal and root paths exist. Only the reports folder is created for you.
