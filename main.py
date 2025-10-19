"""Main entry point for skill scraper workflow."""

import sys
from loguru import logger

from scraper import RepoScraper
from storage import RepoStorage
from ui import RepoSelector
from skill_generator import SkillGenerator


def setup_logging():
    """Configure loguru logger."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "skill_scraper.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )


def main():
    """Main workflow for skill scraper."""
    setup_logging()
    logger.info("Starting skill scraper workflow")

    scraper = RepoScraper()
    storage = RepoStorage()
    ui = RepoSelector()
    skill_gen = SkillGenerator()

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

            logger.info(f"Found {len(repos)} repositories")

            if ui.confirm_action("Fetch detailed descriptions? (This may take a while)"):
                logger.info("Fetching repository details...")
                for i, repo in enumerate(repos):
                    logger.info(f"Fetching details for {repo['full_name']} ({i+1}/{len(repos)})")
                    scraper.fetch_repo_details(repo)

            storage.save_repos(repos)
            logger.info("Saved repositories to repos.json")

        elif action == "load":
            if not storage.exists():
                logger.error("No repos.json file found. Please scrape a repository first.")
                return

            repos = storage.load_repos()

            if not repos:
                logger.error("No repositories in storage")
                return

        selected = ui.select_repos(repos)

        if not selected:
            logger.info("No repositories selected")
            return

        logger.info(f"Installing {len(selected)} skills...")

        successful = 0
        failed = 0

        for repo in selected:
            if skill_gen.generate_skill(repo):
                successful += 1
            else:
                failed += 1

        ui.show_summary(len(selected), successful, failed)

        logger.info(f"Workflow completed. Added {successful} skills to {skill_gen.skills_dir}")

    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        print("\nWorkflow cancelled")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
