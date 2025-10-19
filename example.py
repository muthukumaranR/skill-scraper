"""Example usage of the skill scraper programmatically."""

from loguru import logger
from scraper import RepoScraper
from storage import RepoStorage
from skill_generator import SkillGenerator


def example_scrape_and_install():
    """Example: Scrape an awesome list and install specific skills."""
    logger.info("Starting example workflow")

    scraper = RepoScraper()
    storage = RepoStorage("example_repos.json")
    skill_gen = SkillGenerator()

    awesome_url = "https://github.com/sindresorhus/awesome-python"
    logger.info(f"Scraping {awesome_url}")

    repos = scraper.scrape_awesome_repo(awesome_url)
    logger.info(f"Found {len(repos)} repositories")

    for i, repo in enumerate(repos[:5]):
        logger.info(f"Fetching details for {repo['full_name']} ({i+1}/5)")
        scraper.fetch_repo_details(repo)

    storage.save_repos(repos)
    logger.info(f"Saved {len(repos)} repositories")

    selected_repos = repos[:3]
    logger.info(f"Installing {len(selected_repos)} skills")

    for repo in selected_repos:
        success = skill_gen.generate_skill(repo)
        if success:
            logger.info(f"Installed skill: {repo['full_name']}")
        else:
            logger.warning(f"Skipped (already exists): {repo['full_name']}")

    scraper.close()
    logger.info("Example workflow completed")


def example_load_and_filter():
    """Example: Load from storage and filter repositories."""
    storage = RepoStorage()

    if not storage.exists():
        logger.error("No repos.json found. Run main.py first or use example_scrape_and_install()")
        return

    repos = storage.load_repos()
    logger.info(f"Loaded {len(repos)} repositories")

    python_repos = [r for r in repos if 'python' in r.get('description', '').lower()]
    logger.info(f"Found {len(python_repos)} Python-related repositories")

    skill_gen = SkillGenerator()

    for repo in python_repos[:5]:
        skill_gen.generate_skill(repo)

    logger.info("Installed Python-related skills")


def example_list_skills():
    """Example: List all installed skills."""
    skill_gen = SkillGenerator()
    skills = skill_gen.list_installed_skills()

    logger.info(f"Found {len(skills)} installed skills:")
    for skill in skills:
        logger.info(f"  - {skill}")


if __name__ == "__main__":
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), format="{message}", colorize=True, level="INFO")

    print("\n=== Example 1: Scrape and Install ===\n")

    print("\n=== Example 2: List Skills ===\n")
    example_list_skills()
