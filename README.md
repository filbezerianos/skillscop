# SkillsCop

SkillsCop is a command line tool that keeps a collection of AI agent skills tidy. It finds skills that say nearly the same thing, and skills at a lower level that contradict the rules set above them.

Skills are plain Markdown files, and they pile up fast. Teams copy each other's, people write personal variants, and sooner or later a personal skill quietly disagrees with a team or enterprise policy. I built SkillsCop to make that visible before it causes confusion.

Everything runs locally. Skill files are read from your disk and the models run through [Ollama](https://ollama.com), so nothing is sent to an external service.

## What it does

SkillsCop has three modes:

| Mode | What it does |
|---|---|
| `validate-settings` | Checks your `settings.json`: the paths exist and the thresholds are valid. |
| `check-similarity` | Finds pairs of skills that are near duplicates, comparing both the full text and the `description` in the front matter. Uses TF-IDF cosine similarity. |
| `check-conflicts` | Finds lower level skills that contradict higher level ones. A local model scores each pair, and pairs above your threshold get a written explanation. |

Skills belong to one of three levels, and the higher level always wins:

```
enterprise  >  team  >  personal
```

`check-conflicts` compares enterprise against team and personal, and team against personal.

## Requirements

- Python 3.10 or later
- [Ollama](https://ollama.com) installed and running, for `check-conflicts`
- The Ollama models used by `check-conflicts`:
  - `d1`, which screens each pair and returns the conflict probability
  - `gemma4:e2b`, which writes the explanation for flagged pairs

```
ollama pull gemma4:e2b
ollama pull d1
```

`check-similarity` does not need Ollama.

## Getting started

```
git clone https://github.com/filbezerianos/skillscop.git
cd skillscop
pip install -r requirements.txt
```

Copy the default settings and edit them:

```
copy settings.default.json settings.json      # Windows
cp settings.default.json settings.json        # macOS / Linux
```

`settings.json` is ignored by Git, so your local paths are never committed.

## Configuration

```json
{
    "paths": {
        "enterprise_skills_path": "path/to/enterprise",
        "team_skills_path": "path/to/team",
        "personal_skills_path": "path/to/personal",
        "skills_root_path": "path/to/all-skills",
        "reports_export_path": "path/to/reports"
    },
    "thresholds": {
        "file_cosine_similarity_threshold": 0.75,
        "description_cosine_similarity_threshold": 0.75,
        "instructions_conflict_threshold": 0.7
    }
}
```

| Setting | Used by | Purpose |
|---|---|---|
| `enterprise_skills_path`, `team_skills_path`, `personal_skills_path` | `check-conflicts` | Folders holding the skills of each level |
| `skills_root_path` | `check-similarity` | Folder searched for similar skills, including subfolders |
| `reports_export_path` | both | Where the CSV reports are written (created if missing) |
| `file_cosine_similarity_threshold` | `check-similarity` | Flag pairs whose full text scores at or above this value |
| `description_cosine_similarity_threshold` | `check-similarity` | Flag pairs whose descriptions score at or above this value |
| `instructions_conflict_threshold` | `check-conflicts` | Flag pairs whose conflict probability is above this value |

Lower thresholds flag more pairs, higher thresholds flag fewer. The defaults are a reasonable starting point.

## Usage

```
python skillscop.py validate-settings
python skillscop.py check-similarity
python skillscop.py check-conflicts
```

Only `.md` and `.txt` files are read. For `check-similarity`, add a `description` to the YAML front matter of each skill:

```markdown
---
name: example-skill
description: One sentence on what the skill does and when to use it.
---

The skill instructions go here.
```

## Reports

Each run that finds something writes a timestamped CSV to `reports_export_path`.

**`similarity-YYYYMMDD-HHMMSS.csv`**

| Column | Meaning |
|---|---|
| `content_similarity_score` | Cosine similarity of the full text (0 to 1) |
| `description_similarity_score` | Cosine similarity of the descriptions (0 to 1) |
| `file_a`, `file_b` | The two files |

**`conflicts-YYYYMMDD-HHMMSS.csv`**

| Column | Meaning |
|---|---|
| `conflict_probability` | The model's score that the lower skill contradicts the higher one |
| `high_level`, `high_path` | Level and file of the higher priority skill |
| `low_level`, `low_path` | Level and file of the lower priority skill |
| `explanation` | A written description of the conflicting instructions |

## Logs

Every run writes a log file to `logs/`, named `skillscop-YYYYMMDD-HHMMSS.log`. It records each model call with the pair compared, the score and the time taken. See [`logs/README.md`](logs/README.md). Logs contain your file paths, so review them before sharing.

## Good to know

- **Similarity is lexical.** TF-IDF compares the words used, so two skills that say the same thing in very different words can score low.
- **Conflict detection is a screening aid.** A local model can be wrong in both directions. Treat the report as a list of pairs worth a human look, not a verdict.
- **Run time grows quickly.** `check-conflicts` calls a model for every pair across levels, so large collections take a while. The progress bar shows the remaining time.
- **Your data stays local.** Both the similarity and conflict checks run on your machine.

## Project layout

```
skillscop.py             the command line tool
prompts/                 prompt templates used by check-conflicts
settings.default.json    default settings, copy to settings.json
data/                    optional home for your own skills (see data/README.md)
logs/                    run logs (see logs/README.md)
```

## Licence

Apache License 2.0. See [`LICENSE`](LICENSE).
