"""Playwright-based web crawler for extracting job postings from company websites."""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from models.job import JobPosting
from src.id_generation import generate_job_id
from src.parsers.html_to_markdown import html_to_markdown

logger = logging.getLogger(__name__)


class Crawler:
    """Multi-site job crawler using Playwright."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        """
        Initialize the Crawler.

        Args:
            headless: Run browser in headless mode
            timeout_ms: Navigation timeout in milliseconds
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright: Any = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def initialize(self) -> None:
        """Initialize Playwright browser and context."""
        logger.info("Initializing Playwright browser")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()

    async def close(self) -> None:
        """Close browser and context."""
        logger.info("Closing Playwright browser")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def crawl_company(
        self,
        company_name: str,
        url: str,
        selectors: Dict[str, str],
        crawler_config: Optional[Dict[str, Any]] = None,
    ) -> List[JobPosting]:
        """
        Crawl a company's career page and extract job postings.

        Args:
            company_name: Name of company
            url: Career page URL
            selectors: CSS selectors for job elements {job_container, title, location, link}
            crawler_config: Optional config with wait_for_selector, delay_ms, etc.

        Returns:
            List of extracted JobPosting objects
        """
        if not self.browser or not self.context:
            await self.initialize()

        crawler_config = crawler_config or {}
        wait_selector = crawler_config.get("wait_for_selector", selectors.get("job_container"))
        delay_ms = crawler_config.get("delay_ms", 2000)

        try:
            logger.info(f"Crawling {company_name} at {url}")
            if not self.context:
                raise RuntimeError("Browser context not initialized")
            page = await self.context.new_page()
            page.set_default_timeout(self.timeout_ms)

            await page.goto(url, wait_until="networkidle")
            logger.debug(f"Page loaded for {company_name}")

            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                    logger.debug(f"Found selector: {wait_selector}")
                except Exception as e:
                    logger.warning(f"Selector {wait_selector} not found: {e}")

            await page.wait_for_timeout(delay_ms)

            job_containers = await page.query_selector_all(selectors["job_container"])
            logger.info(f"Found {len(job_containers)} job containers")

            jobs: List[JobPosting] = []
            max_jobs = crawler_config.get("max_jobs_debug", None)
            for i, container in enumerate(job_containers, 1):
                if max_jobs and i > max_jobs:
                    logger.debug(f"Stopping at {max_jobs} jobs (debug mode)")
                    break
                try:
                    job = await self._extract_job_from_container(
                        page, container, company_name, selectors, url, crawler_config
                    )
                    if job:
                        jobs.append(job)
                        logger.debug(f"Extracted job {i}/{len(job_containers)}: {job.title}")
                except Exception as e:
                    logger.warning(f"Failed to extract job {i}: {e}")

            await page.close()
            logger.info(f"Successfully crawled {len(jobs)} jobs from {company_name}")
            return jobs

        except Exception as e:
            logger.error(f"Error crawling {company_name}: {e}")
            return []

    async def _extract_job_from_container(
        self, page: Page, container: Any, company_name: str, selectors: Dict[str, str],
        base_url: str = "", crawler_config: Optional[Dict[str, Any]] = None
    ) -> Optional[JobPosting]:
        """Extract job details from a single job container element."""
        try:
            crawler_config = crawler_config or {}
            title = await self._extract_text(container, selectors.get("title"))
            location = await self._extract_text(container, selectors.get("location"))
            link = await self._extract_link(container, selectors.get("link"))

            logger.debug(f"title={title}, link={link}, fetch_detail={crawler_config.get('fetch_detail')}")

            if not title:
                logger.warning("No title found in container")
                return None

            # Convert relative URLs to absolute
            if link and base_url:
                link = urljoin(base_url, link)

            description = ""
            requirements = None

            # Fetch detail page if enabled
            fetch_detail = crawler_config.get("fetch_detail")
            logger.debug(f"fetch_detail={fetch_detail}, link exists={link is not None}")
            if fetch_detail and link:
                logger.debug(f"Calling _fetch_job_detail for {link}")
                description, requirements = await self._fetch_job_detail(
                    link, selectors
                )
            else:
                logger.debug(f"Skipping detail fetch (fetch_detail={fetch_detail}, link={link is not None})")

            # Generate stable, unique job ID
            generated_id = generate_job_id(
                company=company_name,
                title=title,
                location=location or "Not specified",
                url=link,
            )

            return JobPosting(
                id=generated_id,
                title=title,
                company=company_name,
                location=location or "Not specified",
                url=link,
                description=description,
                requirements=requirements,
                salary_min=None,
                salary_max=None,
                posted_date=None,
                status="pending_review",
                crawled_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.warning(f"Error extracting job from container: {e}")
            import traceback
            logger.debug(f"Exception traceback: {traceback.format_exc()}")
            return None

    def _normalize_description(self, description: str) -> str:
        """
        Normalize job description by converting HTML to Markdown.

        Uses the shared html_to_markdown() utility so that structural
        formatting (headings, lists, etc.) is preserved instead of
        collapsing into a flat, ambiguous run of text.
        """
        if not description:
            return ""
        markdown = html_to_markdown(description)
        return self._add_markdown_section_headers(markdown) if markdown else markdown

    # Standalone lines matching these phrases (case-insensitive, after
    # stripping bold markers / trailing colon) are synthesized into
    # "## " section headers when the source HTML lacks real heading tags.
    _SECTION_HEADER_KEYWORDS = frozenset(
        {
            # qualifications
            "qualifications",
            "desired qualifications",
            "preferred qualifications",
            "minimum qualifications",
            "essential qualifications",
            # requirements
            "requirements",
            "must-have",
            "must haves",
            "must-haves",
            "nice-to-have",
            "nice-to-haves",
            "nice to have",
            "nice to haves",
            "needed",
            # skills
            "skills",
            "technical skills",
            "core skills",
            "competencies",
            # knowledge
            "knowledge",
            "understanding",
            # responsibilities
            "responsibilities",
            "what you'll do",
            "duties",
            "accountabilities",
            # experience
            "experience",
            "background",
            # education
            "education",
            # benefits / compensation
            "benefits",
            "compensation",
            # about-the-role variants
            "about the role",
            "about this role",
            "what we're looking for",
        }
    )

    @staticmethod
    def _extract_bold_label(text: str) -> Optional[str]:
        """Return the inner text of a bold-only standalone line, or None.

        Matches Markdown bold (``**label**``) and MarkItDown-escaped bold
        (``\\*\\*label\\*\\*``) wrapping the entire line.
        """
        match = re.match(r"^\\\*\\\*(.+?)\\\*\\\*$", text)
        if match:
            return match.group(1).strip()
        match = re.match(r"^\*\*(.+?)\*\*$", text)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_standalone_label(text: str) -> Optional[str]:
        """Return the label of a standalone plain/bold line, or None.

        Excludes list items, headers, and table rows so only genuine
        heading-like lines are considered.
        """
        bold_label = Crawler._extract_bold_label(text)
        if bold_label is not None:
            return bold_label
        if text.startswith(("#", "-", "*", "+", ">", "|")) or re.match(r"^\d+\.\s", text):
            return None
        return text

    @classmethod
    def _synthesize_keyword_headers(cls, lines: List[str]) -> None:
        """Step 1: standalone lines matching a known section keyword -> '## Header'.

        Mutates ``lines`` in place.
        """
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            label = cls._extract_standalone_label(stripped)
            if label is None:
                continue
            normalized = label.rstrip(":").strip()
            if normalized.replace("’", "'").lower() in cls._SECTION_HEADER_KEYWORDS:
                lines[i] = f"## {normalized}"

    @classmethod
    def _synthesize_bold_subsection_headers(cls, lines: List[str]) -> None:
        """Step 2: bold-only line followed by non-empty, non-header content -> '### Subsection'.

        Mutates ``lines`` in place.
        """
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            label = cls._extract_bold_label(stripped)
            if label is None:
                continue
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines):
                continue
            next_stripped = lines[j].strip()
            if next_stripped and not next_stripped.startswith("#"):
                lines[i] = f"### {label.rstrip(':').strip()}"

    @staticmethod
    def _synthesize_colon_subsection_headers(lines: List[str]) -> None:
        """Step 3: any remaining non-header line ending in ':' -> '### Subsection'.

        Mutates ``lines`` in place.
        """
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
                continue
            label = stripped[:-1].strip()
            if not label:
                continue
            lines[i] = f"### {label}"

    def _add_markdown_section_headers(self, markdown: str) -> str:
        """
        Synthesize "## "/"### " section headers from keyword, bold, and
        colon-terminated standalone lines when the source HTML lacked real
        heading tags.

        Runs three passes in sequence:
        1. Standalone lines matching a known section keyword (plain, bold,
           or MarkItDown-escaped bold, with an optional trailing colon)
           become "## <Header>".
        2. Remaining bold-only standalone lines followed by non-empty,
           non-header content become "### <Subsection>".
        3. Remaining non-header lines ending in ":" become
           "### <Subsection>".
        """
        lines = markdown.split("\n")
        self._synthesize_keyword_headers(lines)
        self._synthesize_bold_subsection_headers(lines)
        self._synthesize_colon_subsection_headers(lines)
        return "\n".join(lines)

    async def _extract_text(self, element: Any, selector: Optional[str]) -> Optional[str]:
        """Extract text from element using selector."""
        if not selector:
            return None
        try:
            sub_element = await element.query_selector(selector)
            if sub_element:
                text = await sub_element.text_content()
                return text.strip() if text else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
        return None

    async def _extract_html(self, element: Any, selector: Optional[str]) -> Optional[str]:
        """Extract inner HTML from element using selector."""
        if not selector:
            return None
        try:
            sub_element = await element.query_selector(selector)
            if sub_element:
                html = await sub_element.inner_html()
                return html.strip() if html else None
        except Exception as e:
            logger.debug(f"Error extracting HTML with selector {selector}: {e}")
        return None

    async def _extract_link(self, element: Any, selector: Optional[str]) -> Optional[str]:
        """Extract href from element using selector."""
        if not selector:
            return None
        try:
            sub_element = await element.query_selector(selector)
            if sub_element:
                href: str | None = await sub_element.get_attribute("href")
                return href
        except Exception as e:
            logger.debug(f"Error extracting link with selector {selector}: {e}")
        return None

    async def _fetch_job_detail(
        self, job_url: str, selectors: Dict[str, str]
    ) -> tuple[str, Optional[str]]:
        """Fetch job description and requirements from detail page."""
        if not self.context:
            logger.debug("No context available")
            return "", None

        detail_page = None
        try:
            logger.debug(f"Fetching detail for {job_url}")
            detail_page = await self.context.new_page()
            detail_page.set_default_timeout(self.timeout_ms)
            await detail_page.goto(job_url, wait_until="networkidle")
            await detail_page.wait_for_timeout(1000)
            logger.debug("Page loaded, extracting description")

            description = ""
            requirements = None

            # Try to extract description
            desc_selector = selectors.get("description_selector")
            if desc_selector:
                desc_elem = await detail_page.query_selector(desc_selector)
                if desc_elem:
                    # Check if element is an iframe
                    tag_name = await desc_elem.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "iframe":
                        # For iframe: query selector within the frame
                        inner_selector = selectors.get("inner_description_selector")
                        if inner_selector:
                            description = await self._fetch_iframe_via_frame(detail_page, inner_selector)
                        else:
                            # Fallback: get all text from iframe body
                            description = await self._fetch_iframe_via_frame(detail_page, None)
                    else:
                        # Regular element - extract HTML (converted to markdown below)
                        desc_html = await desc_elem.inner_html()
                        description = desc_html.strip() if desc_html else ""

            # Try to extract requirements
            req_selector = selectors.get("requirements_selector")
            if req_selector:
                req_elem = await detail_page.query_selector(req_selector)
                if req_elem:
                    req_text = await req_elem.text_content()
                    requirements = req_text.strip() if req_text else None

            # Convert HTML description to Markdown (iframe-sourced text passes through unchanged)
            description = self._normalize_description(description)

            logger.debug(f"Fetched detail: {len(description)} chars")
            return description, requirements

        except Exception as e:
            logger.debug(f"Error fetching job detail: {e}")
            import traceback
            logger.info(f"DEBUG: Traceback: {traceback.format_exc()}")
            return "", None
        finally:
            if detail_page:
                await detail_page.close()

    async def _fetch_iframe_via_frame(self, page: Page, inner_selector: Optional[str] = None) -> str:
        """Access iframe content via Playwright frame API."""
        try:
            # Wait for iframe to load
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(500)

            # Get all frames from page
            frames = page.frames
            logger.debug(f"Found {len(frames)} frames on page")

            # Try each frame to find content
            for i, frame in enumerate(frames):
                try:
                    if inner_selector:
                        # Query for specific selector within frame
                        elem = await frame.query_selector(inner_selector)
                        if elem:
                            content = await elem.text_content()
                            content = content.strip() if content else ""
                            if content:
                                logger.debug(f"Found selector in frame {i}: {len(content)} chars")
                                return content
                    else:
                        # Get all text content from frame body
                        content = await frame.evaluate("() => document.body.innerText")
                        if isinstance(content, str):
                            content_len = len(content.strip())
                            if content_len > 100:
                                logger.debug(f"Using frame {i} with {content_len} chars")
                                return content.strip()
                except Exception as e:
                    logger.debug(f"Frame {i} error: {e}")
                    continue

            logger.debug("No substantial content found in any frame")
            return ""

        except Exception as e:
            logger.debug(f"Error accessing iframe via frame API: {e}")
            return ""

    async def crawl_multiple(
        self, companies: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[JobPosting]]:
        """
        Crawl multiple companies concurrently.

        Args:
            companies: Dict of company_name -> {url, selectors, crawler}

        Returns:
            Dict of company_name -> list of JobPosting objects
        """
        logger.info(f"Crawling {len(companies)} companies")
        await self.initialize()

        results: Dict[str, List[JobPosting]] = {}
        tasks = []

        for company_name, company_config in companies.items():
            task = self.crawl_company(
                company_name=company_name,
                url=company_config["url"],
                selectors=company_config.get("selectors", {}),
                crawler_config=company_config.get("crawler", {}),
            )
            tasks.append((company_name, task))

        for company_name, task in tasks:
            try:
                results[company_name] = await task
            except Exception as e:
                logger.error(f"Error crawling {company_name}: {e}")
                results[company_name] = []

        await self.close()
        return results
