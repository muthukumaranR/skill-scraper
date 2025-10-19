"""Main entry point for skill scraper workflow."""

import sys
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich import box

from scraper import RepoScraper
from storage import RepoStorage
from ui import RepoSelector
from skill_generator import SkillGenerator
from skill_detector import SkillDetector
from skill_extractor import SkillExtractor
from config import ExtractionConfig

console = Console()


def setup_logging():
    """Configure loguru logger."""
    logger.remove()
    logger.add(
        "skill_scraper.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )


def show_banner():
    """Display application banner."""
    banner = r"""[bold cyan]
 ____  _    _ _ _    ____
/ ___|| | _(_) | |  / ___|  ___ _ __ __ _ _ __   ___ _ __
\___ \| |/ / | | |  \___ \ / __| '__/ _` | '_ \ / _ \ '__|
 ___) |   <| | | |   ___) | (__| | | (_| | |_) |  __/ |
|____/|_|\_\_|_|_|  |____/ \___|_|  \__,_| .__/ \___|_|
                                          |_|
[/bold cyan]
[dim]Scrape awesome-* lists and install Claude Code skills[/dim]
"""
    panel = Panel(
        banner,
        box=box.DOUBLE,
        border_style="cyan",
        padding=(0, 2)
    )
    console.print(panel)


def main():
    """Main workflow for skill scraper."""
    setup_logging()
    show_banner()
    logger.info("Starting skill scraper workflow")

    scraper = RepoScraper()
    storage = RepoStorage()
    ui = RepoSelector()
    skill_gen = SkillGenerator()
    detector = SkillDetector()
    extractor = None

    try:
        action = ui.select_action()

        if action == "exit":
            logger.info("Exiting")
            return

        repos = []

        if action == "scrape":
            github_url = ui.get_github_url()

            if not github_url:
                logger.error("No URL provided")
                return

            logger.info(f"Scraping {github_url}")
            repos = scraper.scrape_awesome_repo(github_url)

            if not repos:
                logger.error("No repositories found")
                return

            ui.print_status(f"\n✓ Found [green]{len(repos)}[/green] repositories\n", style="bold")
            logger.info(f"Found {len(repos)} repositories")

            if ui.confirm_action("Fetch detailed descriptions? (This may take a while)"):
                logger.info("Fetching repository details...")
                console.print()  # Space before progress bar

                with ui.show_progress("Fetching repository details", len(repos)) as progress:
                    task = progress.add_task("[cyan]Fetching descriptions...", total=len(repos))

                    for i, repo in enumerate(repos):
                        progress.update(task, description=f"[cyan]Fetching: {repo['full_name']}")
                        logger.debug(f"Fetching details for {repo['full_name']} ({i+1}/{len(repos)})")
                        scraper.fetch_repo_details(repo)
                        progress.advance(task)

                console.print()  # Space after progress bar

            merge_repos = False
            if storage.exists():
                existing = storage.load_repos()
                merge_repos = ui.confirm_repo_merge(len(existing))

            storage.save_repos(repos, merge=merge_repos, source=github_url)

            action = "Merged" if merge_repos else "Saved"
            ui.print_status(f"✓ {action} repositories to repos.json\n", style="green")
            logger.info(f"{action} repositories to repos.json")

        elif action == "load":
            if not storage.exists():
                logger.error("No repos.json file found. Please scrape a repository first.")
                return

            repos = storage.load_repos()

            if not repos:
                ui.print_status("✗ No repositories in storage", style="red bold")
                logger.error("No repositories in storage")
                return

            ui.print_status(f"✓ Loaded [green]{len(repos)}[/green] repositories from storage\n", style="bold")

        config = ui.select_extraction_mode()

        if config.mode in ["extract", "both", "metadata"]:
            config.update_existing = ui.confirm_skill_update()

        extractor = SkillExtractor(config=config)

        detection_results = {}

        if config.auto_detect and config.mode in ["extract", "both"]:
            logger.info("Detecting skill repositories...")
            console.print()  # Space before progress bar

            with ui.show_progress("Detecting skill repositories", len(repos)) as progress:
                task = progress.add_task("[yellow]Analyzing repositories...", total=len(repos))

                for i, repo in enumerate(repos):
                    progress.update(task, description=f"[yellow]Checking: {repo['full_name']}")
                    logger.debug(f"Checking {repo['full_name']} ({i+1}/{len(repos)})")
                    detection_results[repo['full_name']] = detector.detect_skills(repo)
                    progress.advance(task)

            console.print()  # Space after progress bar
            skill_repo_count = sum(1 for r in detection_results.values() if r.get('is_skill_repo'))
            ui.print_status(f"✓ Detected [green]{skill_repo_count}[/green] skill repositories\n", style="bold")

        selected = ui.select_repos(repos, detection_results)

        if not selected:
            ui.print_status("\n✗ No repositories selected", style="yellow bold")
            logger.info("No repositories selected")
            return

        logger.info(f"Processing {len(selected)} repositories...")
        console.print()  # Space before progress bar

        successful = 0
        failed = 0
        total_extracted = 0

        with ui.show_progress("Extracting skills", len(selected)) as progress:
            task = progress.add_task("[green]Extracting skills...", total=len(selected))

            for repo in selected:
                progress.update(task, description=f"[green]Processing: {repo['full_name']}")
                repo_full_name = repo['full_name']
                is_skill_repo = detection_results.get(repo_full_name, {}).get('is_skill_repo', False)

                should_extract = False
                if config.mode == "extract" or (config.mode == "both" and is_skill_repo):
                    if config.confirm_extraction and is_skill_repo:
                        should_extract = ui.confirm_skill_extraction(
                            repo,
                            detection_results[repo_full_name]
                        )
                    else:
                        should_extract = is_skill_repo

                if should_extract:
                    logger.info(f"Extracting skills from {repo_full_name}...")
                    extraction_result = extractor.extract_skills(
                        repo,
                        detection_results.get(repo_full_name, {})
                    )

                    if extraction_result['success']:
                        total_extracted += extraction_result['extracted_count']
                        logger.info(
                            f"Extracted {extraction_result['extracted_count']} skills "
                            f"from {repo_full_name}"
                        )
                    else:
                        logger.warning(f"Failed to extract skills from {repo_full_name}")

                if config.mode in ["metadata", "both"]:
                    if skill_gen.generate_skill(repo, update=config.update_existing):
                        successful += 1
                    else:
                        failed += 1

                progress.advance(task)

        console.print()  # Space after progress bar

        ui.show_summary(
            len(selected),
            successful,
            failed,
            extracted=total_extracted,
            extraction_mode=config.mode
        )

        logger.info(f"Workflow completed. Mode: {config.mode}")

    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        print("\nWorkflow cancelled")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {e}")

    finally:
        scraper.close()
        detector.close()


if __name__ == "__main__":
    main()
