import click
import csv
import frontmatter
import json
import logging
import ollama
import sys
import time
from datetime import datetime
from itertools import combinations
from rich.console import Console
from rich.progress import Progress, BarColumn, MofNCompleteColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Set paths
SETTINGS_PATH = Path(__file__).parent / "settings.json"
PROMPTS_PATH = Path(__file__).parent / "prompts"
LOGS_PATH = Path(__file__).parent / "logs"

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
log_path = LOGS_PATH / f"skillscop-{timestamp}.log"

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("skillscop")

console = Console()

# Read the settings and check if any of the required values is null
def validate_settings(settings_path=SETTINGS_PATH):

    console.print("\n[bold]VALIDATING Settings.json[/bold]")

    console.print("Checking Paths...")

    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    with open(settings_path, encoding="utf-8") as f:

        settings = json.load(f)

        # Enterprise skills path
        enterprise_skills_path = settings["paths"]["enterprise_skills_path"]
        if enterprise_skills_path is None:
            raise ValueError("Enterprise skills path is not set in settings.json")
        elif not Path(enterprise_skills_path).exists():
            raise FileNotFoundError(f"Enterprise skills path not found: {enterprise_skills_path}")
        else:
            console.print(f"Enterprise skills path: {enterprise_skills_path}")

        # Teams skills path
        team_skills_path = settings["paths"]["team_skills_path"]
        if team_skills_path is None:
            raise ValueError("Team skills path is not set in settings.json")
        elif not Path(team_skills_path).exists():
            raise FileNotFoundError(f"Team skills path not found: {team_skills_path}")
        else:
            console.print(f"Teams skills path: {team_skills_path}")

        # Personal skills path
        personal_skills_path = settings["paths"]["personal_skills_path"]
        if personal_skills_path is None:
            raise ValueError("Personal skills path is not set in settings.json")
        elif not Path(personal_skills_path).exists():
            raise FileNotFoundError(f"Personal skills path not found: {personal_skills_path}")
        else:
            console.print(f"Personal skills path: {personal_skills_path}")

        # Skills root path
        skills_root_path = settings["paths"]["skills_root_path"]
        if skills_root_path is None:
            raise ValueError("Skills root skills path is not set in settings.json")
        elif not Path(skills_root_path).exists():
            raise FileNotFoundError(f"Skills root path not found: {skills_root_path}")
        else:
            console.print(f"Skills root path: {skills_root_path}")

        # Reports export path
        reports_export_path = settings["paths"]["reports_export_path"]
        if reports_export_path is None:
            raise ValueError("Reports export path is not set in settings.json")
        elif not Path(reports_export_path).exists():
            console.print(f"[cyan]Reports export path does not exist: {reports_export_path}[/cyan]")
            console.print("[cyan]Creating it...[/cyan]")

            try:
                Path(reports_export_path).mkdir(parents=True, exist_ok=True)
                console.print(f"[green]Reports export path created: {reports_export_path}[green]")
            except OSError as e:
                raise OSError(f"Error creating reports export directory {reports_export_path}: {e}")


        console.print("\nChecking Thresholds...")

        # Files Cosine similarity threshold
        file_cosine_similarity_threshold = settings["thresholds"]["file_cosine_similarity_threshold"]
        if not isinstance(file_cosine_similarity_threshold, (int, float)) or isinstance(file_cosine_similarity_threshold, bool):
            raise ValueError(f"file_cosine_similarity_threshold must be a number: {file_cosine_similarity_threshold}")
        elif not 0 <= file_cosine_similarity_threshold <= 1:
            raise ValueError(f"file_cosine_similarity_threshold must be between 0 and 1: {file_cosine_similarity_threshold}")
        elif round(file_cosine_similarity_threshold, 2) != file_cosine_similarity_threshold:
            raise ValueError(f"file_cosine_similarity_threshold must have at most 2 decimal places: {file_cosine_similarity_threshold}")
        else:
            console.print(f"file_cosine_similarity_threshold value: {file_cosine_similarity_threshold}")

        # Description Cosine similarity threshold
        description_cosine_similarity_threshold = settings["thresholds"]["description_cosine_similarity_threshold"]
        if not isinstance(description_cosine_similarity_threshold, (int, float)) or isinstance(description_cosine_similarity_threshold, bool):
            raise ValueError(f"description_cosine_similarity_threshold must be a number: {description_cosine_similarity_threshold}")
        elif not 0 <= description_cosine_similarity_threshold <= 1:
            raise ValueError(f"description_cosine_similarity_threshold must be between 0 and 1: {description_cosine_similarity_threshold}")
        elif round(description_cosine_similarity_threshold, 2) != description_cosine_similarity_threshold:
            raise ValueError(f"description_cosine_similarity_threshold must have at most 2 decimal places: {description_cosine_similarity_threshold}")
        else:
            console.print(f"description_cosine_similarity_threshold value: {description_cosine_similarity_threshold}")

        # Instructions conflict threshold
        instructions_conflict_threshold = settings["thresholds"]["instructions_conflict_threshold"]
        if not isinstance(instructions_conflict_threshold, (int, float)) or isinstance(instructions_conflict_threshold, bool):
            raise ValueError(f"instructions_conflict_threshold must be a number: {instructions_conflict_threshold}")
        elif not 0 <= instructions_conflict_threshold <= 1:
            raise ValueError(f"instructions_conflict_threshold must be between 0 and 1: {instructions_conflict_threshold}")
        elif round(instructions_conflict_threshold, 2) != instructions_conflict_threshold:
            raise ValueError(f"instructions_conflict_threshold must have at most 2 decimal places: {instructions_conflict_threshold}")
        else:
            console.print(f"instructions_conflict_threshold value: {instructions_conflict_threshold}")
            


def create_check_conflicts_prompt(higher_level, higher_label, higher_text, lower_level, lower_label, lower_text):

    prompt_template = (PROMPTS_PATH / "check-conflicts.md").read_text(encoding="utf-8")

    return prompt_template.format(
        higher_level=higher_level,
        higher_label=higher_label,
        higher_text=higher_text,
        lower_level=lower_level,
        lower_label=lower_label,
        lower_text=lower_text,
    )



def get_conflicts_details_prompt(higher_level, higher_label, higher_text, lower_level, lower_label, lower_text):

    prompt_template = (PROMPTS_PATH / "get-conflicts-details.md").read_text(encoding="utf-8")
    
    return prompt_template.format(
        higher_level=higher_level,
        higher_label=higher_label,
        higher_text=higher_text,
        lower_level=lower_level,
        lower_label=lower_label,
        lower_text=lower_text,
    )



@click.command
@click.argument("mode", type=click.Choice(["validate-settings", "check-similarity", "check-conflicts"]))
def main(mode):

    try:
        validate_settings()
    except (FileNotFoundError, ValueError, OSError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # The validation has passed load the settings.json
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        settings = json.load(f)
        
    enterprise_skills_path = settings["paths"]["enterprise_skills_path"]
    team_skills_path = settings["paths"]["team_skills_path"]
    personal_skills_path = settings["paths"]["personal_skills_path"]
    skills_root_path = Path(settings["paths"]["skills_root_path"])
    reports_export_path = settings["paths"]["reports_export_path"]
    file_cosine_similarity_threshold = settings["thresholds"]["file_cosine_similarity_threshold"]
    description_cosine_similarity_threshold = settings["thresholds"]["description_cosine_similarity_threshold"]
    instructions_conflict_threshold = settings["thresholds"]["instructions_conflict_threshold"]

    # Allows files extensions
    files_extensions = [".txt", ".md"]     



    if mode == "validate-settings":
        console.print("\nCompleted settings.json validation. No issues found.", style="green")



    elif mode == "check-similarity":

        console.print(f"\n[bold]CHECKING SKILLS SIMILARITIES IN FOLDER: {skills_root_path}[/bold]")
        
        files_to_compare = []

        # Collect the files to check
        for f in sorted(skills_root_path.rglob("*")):
            if f.is_file() and f.suffix.lower() in files_extensions:
                files_to_compare.append(f)

        if len(files_to_compare) < 2:
            raise SystemExit(f"Need at least 2 files, found {len(files_to_compare)} in: {skills_root_path}")

        console.print(f"[cyan]Found {len(files_to_compare)} files.[/cyan]")

        # Read the files and get the full text and description
        texts_to_compare = []
        descriptions_to_compare = []
        for f in files_to_compare:
            texts_to_compare.append(f.read_text(encoding="utf-8", errors="replace"))

            file_text = frontmatter.load(f)
            file_description = file_text.get("description", "")
            #file_name = file_text.get("name", "")

            descriptions_to_compare.append(file_description)


        # Vectorise once in the whole corpus
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        texts_tfidf = vec.fit_transform(texts_to_compare)
        descriptions_tfidf = vec.fit_transform(descriptions_to_compare)

        # Similarity matrix for all pairs
        texts_sim = cosine_similarity(texts_tfidf)
        descriptions_sim = cosine_similarity(descriptions_tfidf)

        # Collect each unique pair
        results = []
        
        n_files = len(files_to_compare)
        total_comparisons = n_files * (n_files - 1) // 2

        console.print(f"[cyan]Total comparisons: {total_comparisons}.[/cyan]")

        with Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Comparing files...", total=total_comparisons)
            
            for i in range(len(files_to_compare)):
                for j in range(i + 1, len(files_to_compare)):
                    files_similarity_score = texts_sim[i][j]
                    descriptions_similarity_score = descriptions_sim[i][j]

                    if files_similarity_score >= file_cosine_similarity_threshold or descriptions_similarity_score >= description_cosine_similarity_threshold:
                        results.append((round(float(files_similarity_score), 2), round(float(descriptions_similarity_score), 2), files_to_compare[i], files_to_compare[j]))

                    progress.advance(task)

        if len(results) <= 0:
            console.print(f"[green]No similar files or descriptions, based on file_cosine_similarity_threshold: {file_cosine_similarity_threshold} and description_cosine_similarity_threshold: {description_cosine_similarity_threshold}[/green]")
        else:
            console.print(f"[cyan]{len(results)} similar files based on file_cosine_similarity_threshold: {file_cosine_similarity_threshold} and description_cosine_similarity_threshold: {description_cosine_similarity_threshold}[cyan]")

            # results_table = Table(title="Similarity Results")
            # results_table.add_column("Content")
            # results_table.add_column("Description")
            # results_table.add_column("File A")
            # results_table.add_column("File B")
            

            # results.sort(reverse=True, key=lambda r: r[0])

            # for files_similarity_score, descriptions_similarity_score, fa, fb in results:
            #     #console.print(f"{files_similarity_score:.2f}   {descriptions_similarity_score:.2f}    {fa.relative_to(skills_root_path)}   {fb.relative_to(skills_root_path)}")
            #     results_table.add_row(f"{files_similarity_score:.2f}", f"{descriptions_similarity_score:.2f}", f"{fa.relative_to(skills_root_path)}", f"{fb.relative_to(skills_root_path)}")

            # console.print(results_table)

            # Export results to csv
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            csv_path = Path(reports_export_path) / f"similarity-{timestamp}.csv"

            columns = ["content_similarity_score", "description_similarity_score", "file_a", "file_b"]

            try:
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(results)

                console.print(f"[green]Report exported at: {csv_path}[/green]")
            except OSError as e:
                console.print(f"[red]Errors exporting report at: {csv_path}[/red]") 






    elif mode == "check-conflicts":

        console.print("\n[bold]CHECKING FOR SKILL CONFLICTS.[/bold]")

        # Highest priority first
        level_paths = {
            "enterprise": Path(enterprise_skills_path),
            "team": Path(team_skills_path),
            "personal": Path(personal_skills_path),
        }

        # {level: [(skill_name, text), ...]} for each hierarchy level.
        skills = {}

        for level, level_path in level_paths.items():
            skills[level] = []
            for f in sorted(level_path.rglob("*")):
                if f.is_file() and f.suffix.lower() in files_extensions:
                    label = f.relative_to(level_path).as_posix()
                    text = f.read_text(encoding="utf-8", errors="replace")
                    skills[level].append((label, text))

  
        # enterprise, team, personal (highest priority first)
        level_names = list(skills.keys())

        results = []

        total_comparisons = sum(
            len(skills[higher]) * len(skills[lower])
            for higher, lower in combinations(level_names, 2)
        )
        console.print(f"[cyan]Total comparisons: {total_comparisons}[/cyan]")

        with Progress(
                TextColumn("{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
            task = progress.add_task("Comparing skills...", total=total_comparisons)

            for i, higher_level in enumerate(level_names):
                for lower_level in level_names[i + 1:]:
                    for higher_label, higher_text in skills[higher_level]:
                        for lower_label, lower_text in skills[lower_level]:

                            #pair = f"{higher_level}/{higher_label} vs {lower_level}/{lower_label}"
                            #console.print(f"Comparing {pair}...")

                            decision_model_prompt = create_check_conflicts_prompt(higher_level, higher_label, higher_text, lower_level, lower_label, lower_text)
                            #console.print(len(decision_model_prompt))
                            #console.print(f"{len(decision_model_prompt) // 4}")

                            try:
                                start_d1 = time.perf_counter()

                                response = ollama.systemone(
                                    model = 'd1',
                                    state = decision_model_prompt,
                                    questions = {
                                        'conflicts_check': {
                                        'type': 'noul',
                                        'instructions': 'Do they contain conflicting instructions? Yes or No?',
                                        'criteria': {
                                            'true': 'Lower level text contains conflicting instructions to higher level text.',
                                            'false': 'Lower level text does not contains conflicting instructions to higher level text.',
                                            },
                                        },
                                    }
                                )
                                #console.print(f"Conflicting instructions probability: {response.answers['conflicts_check'].noul}")

                                conflict_probability = response.answers['conflicts_check'].noul

                                elapsed_d1 = time.perf_counter() - start_d1
                                logger.info("systemone model=d1 pair=%s %s vs %s %s probability=%.2f elapsed=%.2fs", higher_level, higher_label, lower_level, lower_label, conflict_probability, elapsed_d1)

                                if conflict_probability > instructions_conflict_threshold:
                                    #console.print(f"{higher_level} IN {higher_label} vs {lower_level} IN {lower_label}   Conflicting instructions probability: {conflict_probability}")

                                    details_prompt_details = get_conflicts_details_prompt(higher_level, higher_label, higher_text, lower_level, lower_label, lower_text)

                                    start_gemma = time.perf_counter()

                                    response_details = ollama.chat(
                                        model = "gemma4:e2b",
                                        messages=[{"role": "user", "content": details_prompt_details}],
                                    )
                                    conflict_summary = response_details["message"]["content"]
                                    #console.print(conflict_summary)

                                    elapsed_gemma = time.perf_counter() - start_gemma
                                    logger.info("chat model=gemma4:e2b pair=%s %s vs %s %s elapsed=%.2fs", higher_level, higher_label, lower_level, lower_label, elapsed_gemma)

                                    results.append((round(float(conflict_probability), 2), higher_level, higher_label, lower_level, lower_label, conflict_summary))


                            except (ollama.ResponseError, ConnectionError, json.JSONDecodeError) as e:
                                console.print(f"[red]Error:[/red] {e}")
                                logger.exception("Model call failed")
                                sys.exit(1)

                            progress.advance(task)


        if len(results) <= 0:
            console.print(f"[green]No conflicting instructions based on instructions_conflict_threshold: {instructions_conflict_threshold}[/green]")
        else:
            console.print(f"[cyan]{len(results)} skills with possible conflicting instructions based on instructions_conflict_threshold: {instructions_conflict_threshold}[/cyan]")

            # results_table = Table(title="Conflicts Results")
            # results_table.add_column("Conflict Probability")
            # results_table.add_column("High Level")
            # results_table.add_column("Path")
            # results_table.add_column("Low Level")
            # results_table.add_column("Path")
            # results_table.add_column("Summary")

            # results.sort(reverse=True, key=lambda r: r[0])

            # for conflict_probability, high_level, high_path, low_level, low_path, conflict_summary in results:
            #     results_table.add_row(f"{conflict_probability:.2f}", f"{high_level}", f"{high_path}", f"{low_level}", f"{low_path}", f"{conflict_summary}")

            # console.print(results_table)

            # Export results to csv
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            csv_path = Path(reports_export_path) / f"conflicts-{timestamp}.csv"

            columns = ["conflict_probability", "high_level", "high_path", "low_level", "low_path", "explanation"]

            try:
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(results)

                console.print(f"[green]Report exported at: {csv_path}[/green]")
            except OSError as e:
                console.print(f"[red]Errors exporting report at: {csv_path}[/red]") 


    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()