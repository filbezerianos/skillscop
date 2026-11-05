# logs/

Runtime log files written by SkillsCop.

## What goes here

Every time you run `skillscop.py`, it creates a new log file in this folder, named with the start time of the run:

```
skillscop-YYYYMMDD-HHMMSS.log
```

A log file is created for every mode (`validate-settings`, `check-similarity` and `check-conflicts`), but only `check-conflicts` writes entries to it today.

## What is recorded

During `check-conflicts`, each model call is logged as one line with a timestamp and level:

- **Conflict screening:** the `d1` model call for each pair of skills, with the higher and lower level (enterprise, team, personal), the two file paths, the conflict probability and how long the call took.
- **Conflict details:** for pairs above `instructions_conflict_threshold`, the `gemma4:e2b` call that writes the explanation, with the same pair details and the time taken.
- **Failures:** if a model call fails, the full error and stack trace are logged before the run stops.

Use these logs to see which pairs were compared, how each one scored, and how long the models took. The conflict report itself is exported as a CSV to your `reports_export_path`, not to this folder.

## Good to know

- **Not tracked by Git.** Everything here except this README is listed in `.gitignore`, so logs stay on your machine and are never pushed.
- **Do not delete the folder.** The log file is created as soon as the script starts, so the folder must exist or the run will fail.
- **Safe to clean up.** Old log files can be deleted at any time.
- **May contain sensitive information.** Logs include the paths and names of your skill files. Review a log before sharing it.
