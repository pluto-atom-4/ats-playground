#!/usr/bin/env python3
"""Crawler module to extract job listings from company career pages (Issue #309).

Crawls job listing pages, extracts job titles/locations/links, writes per-company
JSON files to data/work/ directory.

Usage:
    python -m src.poc.tweak.crawl_list \\
        --config-dir config_test \\
        --output-dir data/work \\
        --company CarbonRobotics \\
        --headless
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urljoin

from playwright.async_api import Browser, Page, Playwright

from src.poc.tweak.common import (
    GENERIC_FALLBACK_SELECTORS,
    close_browser,
    init_browser,
    load_all_company_configs,
    retry_goto,
    setup_logging,
)

logger = logging.getLogger(__name__)


# ============================================================================
# JOB EXTRACTION
# ============================================================================


async def extract_text(element: Any, selector: Optional[str]) -> Optional[str]:
    """Extract text from element using selector."""
    if not selector:
        return None
    try:
        sub_element = await element.query_selector(selector)
        if sub_element:
            text = await sub_element.text_content()
            return text.strip() if text else None
    except Exception as e:
        logger.debug(f"Error extracting text with selector '{selector}': {e}")
    return None


async def extract_link(element: Any, selector: Optional[str]) -> Optional[str]:
    """Extract href from element using selector."""
    if not selector:
        return None
    try:
        sub_element = await element.query_selector(selector)
        if sub_element:
            href = await sub_element.get_attribute("href")
            return cast(Optional[str], href)
    except Exception as e:
        logger.debug(f"Error extracting link with selector '{selector}': {e}")
    return None


async def extract_job_from_container(
    page: Page,
    container: Any,
    company_name: str,
    selectors: Dict[str, str],
    base_url: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Extract job details from a single job container element.

    Returns dict with title, location, link, or None if extraction fails.
    """
    try:
        title = await extract_text(container, selectors.get("title"))
        location = await extract_text(container, selectors.get("location"))
        link = await extract_link(container, selectors.get("link"))

        if not title:
            logger.debug("Skipping container: no title found")
            return None

        # Convert relative URLs to absolute
        if link and base_url:
            link = urljoin(base_url, link)

        return {
            "title": title,
            "location": location or "",
            "url": link or "",
        }
    except Exception as e:
        logger.debug(f"Error extracting job from container: {e}")
        return None


# ============================================================================
# COMPANY CRAWLING
# ============================================================================


async def crawl_company_jobs(
    browser: Browser,
    company_key: str,
    company_config: Dict[str, Any],
    timeout_ms: int = 30000,
) -> List[Dict[str, Any]]:
    """
    Crawl a company's career page and extract job listings.

    Args:
        browser: Playwright browser instance
        company_key: Company key (e.g., "CarbonRobotics")
        company_config: Company configuration dict with url, selectors, crawler
        timeout_ms: Page navigation timeout in milliseconds

    Returns:
        List of extracted job dicts {title, location, url}
    """
    if not company_config.get("enabled", True):
        logger.info(f"Skipping disabled company: {company_key}")
        return []

    url = company_config.get("url")
    if not url:
        logger.warning(f"Company {company_key} has no URL configured")
        return []

    crawler_config = company_config.get("crawler", {})
    selectors = company_config.get("selectors", {})

    try:
        logger.info(f"Crawling {company_key} at {url}")
        page = await browser.new_page()
        page.set_default_timeout(timeout_ms)

        # Navigate to career page
        if not await retry_goto(page, url, max_attempts=3, timeout_ms=timeout_ms, logger=logger):
            logger.warning(f"Failed to navigate to {company_key} career page")
            await page.close()
            return []

        # Wait for optional selector
        wait_selector = crawler_config.get("wait_for_selector", selectors.get("job_container"))
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
                logger.debug(f"Found wait selector: {wait_selector}")
            except Exception as e:
                logger.warning(f"Wait selector '{wait_selector}' not found: {e}")

        # Delay before extraction
        delay_ms = crawler_config.get("delay_ms", 2000)
        await page.wait_for_timeout(delay_ms)

        # Extract job containers
        job_container_selector = selectors.get("job_container") or GENERIC_FALLBACK_SELECTORS.get("job_container")
        if not job_container_selector:
            logger.error(f"No job container selector found for {company_key}")
            await page.close()
            return []

        job_containers = await page.query_selector_all(job_container_selector)
        logger.info(f"Found {len(job_containers)} job containers in {company_key}")

        jobs: List[Dict[str, Any]] = []
        max_jobs_debug = crawler_config.get("max_jobs_debug")

        for i, container in enumerate(job_containers, 1):
            if max_jobs_debug and i > max_jobs_debug:
                logger.debug(f"Stopping at {max_jobs_debug} jobs (debug mode)")
                break

            try:
                job = await extract_job_from_container(page, container, company_key, selectors, url)
                if job:
                    jobs.append(job)
                    logger.debug(f"Extracted job {i}/{len(job_containers)}: {job['title'][:50]}...")
            except Exception as e:
                logger.warning(f"Failed to extract job {i} from {company_key}: {e}")
                # Continue to next job on failure

        await page.close()
        logger.info(f"Successfully extracted {len(jobs)} jobs from {company_key}")
        return jobs

    except Exception as e:
        logger.error(f"Error crawling {company_key}: {e}")
        return []


# ============================================================================
# MAIN CRAWL FUNCTION
# ============================================================================


async def crawl_all_companies(
    config_dir: str = "config_test",
    output_dir: str = "data/work",
    company_filter: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> int:
    """
    Crawl all enabled companies (or filtered set) and write job listings to JSON.

    Args:
        config_dir: Directory containing config JSON files
        output_dir: Directory to write output JSON files
        company_filter: Optional company key to crawl only one company
        headless: If True, run browser in headless mode
        timeout_ms: Page navigation timeout in milliseconds

    Returns:
        Exit code: 0 = success, 1 = config error, 2 = system/browser error
    """
    logger.info("Starting job listing crawler")
    logger.info(f"Config dir: {config_dir}")
    logger.info(f"Output dir: {output_dir}")

    # Create output directory
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return 1

    # Load config
    try:
        merged_config = load_all_company_configs(config_dir)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Config loading failed: {e}")
        return 1

    # Filter companies
    companies_to_crawl = merged_config
    if company_filter:
        if company_filter not in companies_to_crawl:
            logger.error(f"Company '{company_filter}' not found in config")
            logger.info(f"Available companies: {', '.join(companies_to_crawl.keys())}")
            return 1
        companies_to_crawl = {company_filter: companies_to_crawl[company_filter]}

    logger.info(f"Crawling {len(companies_to_crawl)} companies")

    # Initialize browser
    playwright: Optional[Playwright] = None
    browser: Optional[Browser] = None
    try:
        playwright, browser = await init_browser(headless=headless)
    except RuntimeError as e:
        logger.error(f"Browser initialization failed: {e}")
        return 2

    try:
        # Crawl each company sequentially
        for company_key, company_config in companies_to_crawl.items():
            try:
                jobs = await crawl_company_jobs(
                    browser,
                    company_key,
                    company_config,
                    timeout_ms=timeout_ms,
                )

                # Write output JSON (even if empty)
                output_file = output_path / f"{company_key}_jobs.json"
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(jobs, f, indent=2, ensure_ascii=False)
                    logger.info(f"Wrote {len(jobs)} jobs to {output_file}")
                except Exception as e:
                    logger.error(f"Failed to write {output_file}: {e}")

            except Exception as e:
                logger.error(f"Error processing company {company_key}: {e}")
                # Continue to next company on failure

        logger.info("Crawl completed successfully")
        return 0

    finally:
        await close_browser(playwright, browser)


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


def main() -> int:
    """Parse CLI arguments and run crawler."""
    parser = argparse.ArgumentParser(
        description="Crawl job listings from company career pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl all companies
  python -m src.poc.tweak.crawl_list --config-dir config_test --output-dir data/work

  # Crawl single company
  python -m src.poc.tweak.crawl_list --config-dir config_test --company CarbonRobotics

  # Show available companies
  python -m src.poc.tweak.crawl_list --config-dir config_test --list-companies
        """,
    )

    parser.add_argument(
        "--config-dir",
        type=str,
        default="config_test",
        help="Directory containing company config JSON files (default: config_test)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/work",
        help="Directory to write job listing JSON files (default: data/work)",
    )
    parser.add_argument(
        "--company",
        type=str,
        default=None,
        help="Optional: crawl only one company by key (e.g., CarbonRobotics)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Run browser in headed mode (for debugging)",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Page navigation timeout in milliseconds (default: 30000)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(__name__, level=args.log_level)

    # Run crawler
    try:
        exit_code = asyncio.run(
            crawl_all_companies(
                config_dir=args.config_dir,
                output_dir=args.output_dir,
                company_filter=args.company,
                headless=args.headless,
                timeout_ms=args.timeout_ms,
            )
        )
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
