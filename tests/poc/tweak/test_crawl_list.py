"""Tests for crawl_list.py job extraction and company crawling."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.poc.tweak.crawl_list import crawl_company_jobs, extract_job_from_container, parse_posted_date


class TestParsePostedDate:
    """Test suite for parse_posted_date function."""

    def test_parse_posted_date_none_input(self):
        """Test that None input returns None."""
        result = parse_posted_date(None, datetime(2026, 9, 8, 10, 30))
        assert result is None

    def test_parse_posted_date_empty_string(self):
        """Test that empty string returns None."""
        result = parse_posted_date("", datetime(2026, 9, 8, 10, 30))
        assert result is None

    def test_parse_posted_date_today(self):
        """Test 'Posted Today' returns reference date."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Posted Today", reference)
        assert result == "2026-09-08"

    def test_parse_posted_date_today_case_insensitive(self):
        """Test 'Posted Today' is case-insensitive."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("POSTED TODAY", reference)
        assert result == "2026-09-08"

    def test_parse_posted_date_yesterday(self):
        """Test 'Posted Yesterday' returns reference - 1 day."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Posted Yesterday", reference)
        assert result == "2026-09-07"

    def test_parse_posted_date_yesterday_case_insensitive(self):
        """Test 'Posted Yesterday' is case-insensitive."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("posted yesterday", reference)
        assert result == "2026-09-07"

    def test_parse_posted_date_n_days_ago(self):
        """Test 'Posted N Days Ago' returns reference - N days."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Posted 8 Days Ago", reference)
        assert result == "2026-08-31"

    def test_parse_posted_date_n_days_ago_single_day(self):
        """Test 'Posted 1 Days Ago' (singular 'day' variant)."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Posted 1 Day Ago", reference)
        assert result == "2026-09-07"

    def test_parse_posted_date_n_days_ago_case_insensitive(self):
        """Test 'Posted N Days Ago' is case-insensitive."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("POSTED 5 DAYS AGO", reference)
        assert result == "2026-09-03"

    def test_parse_posted_date_30_plus_days_ago(self):
        """Test 'Posted 30+ Days Ago' returns reference - 30 days."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Posted 30+ Days Ago", reference)
        assert result == "2026-08-09"

    def test_parse_posted_date_30_plus_days_ago_case_insensitive(self):
        """Test 'Posted 30+ Days Ago' is case-insensitive."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("posted 30+ days ago", reference)
        assert result == "2026-08-09"

    def test_parse_posted_date_garbage_text(self):
        """Test that garbage text returns None."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("Some random text", reference)
        assert result is None

    def test_parse_posted_date_whitespace_trimmed(self):
        """Test that leading/trailing whitespace is handled."""
        reference = datetime(2026, 9, 8, 10, 30)
        result = parse_posted_date("  Posted 3 Days Ago  ", reference)
        assert result == "2026-09-05"

    def test_parse_posted_date_month_boundary(self):
        """Test date calculation across month boundary."""
        reference = datetime(2026, 9, 5, 10, 30)
        result = parse_posted_date("Posted 10 Days Ago", reference)
        assert result == "2026-08-26"

    def test_parse_posted_date_year_boundary(self):
        """Test date calculation across year boundary."""
        reference = datetime(2026, 1, 5, 10, 30)
        result = parse_posted_date("Posted 10 Days Ago", reference)
        assert result == "2025-12-26"


class TestExtractJobFromContainer:
    """Test suite for extract_job_from_container function."""

    @pytest.mark.asyncio
    async def test_extract_job_from_container_full_schema(self):
        """Test that extract_job_from_container returns all 12 required fields."""
        # Mock page and container
        page = AsyncMock()
        container = AsyncMock()

        # Mock element queries
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Senior Python Developer")

        location_elem = AsyncMock()
        location_elem.text_content = AsyncMock(return_value="San Francisco, CA")

        link_elem = AsyncMock()
        link_elem.get_attribute = AsyncMock(return_value="https://example.com/jobs/123")

        # Setup container.query_selector to return mocked elements
        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "location":
                return location_elem
            elif selector == "link":
                return link_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        # Call function
        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="Carbon Robotics",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="https://example.com/",
        )

        # Verify all 12 fields are present
        assert result is not None
        expected_fields = {
            "id",
            "title",
            "company",
            "location",
            "url",
            "description",
            "requirements",
            "salary_min",
            "salary_max",
            "posted_date",
            "crawled_at",
            "status",
        }
        assert set(result.keys()) == expected_fields

    @pytest.mark.asyncio
    async def test_extract_job_from_container_id_deterministic(self):
        """Test that same inputs produce identical job IDs (deterministic hashing)."""
        # Mock page and container
        page = AsyncMock()
        container = AsyncMock()

        # Mock element queries
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Python Engineer")

        location_elem = AsyncMock()
        location_elem.text_content = AsyncMock(return_value="Remote")

        link_elem = AsyncMock()
        link_elem.get_attribute = AsyncMock(return_value="https://example.com/jobs/456")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "location":
                return location_elem
            elif selector == "link":
                return link_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        # Call function twice with same inputs
        result1 = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TechCorp",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="https://example.com/",
        )

        result2 = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TechCorp",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="https://example.com/",
        )

        # IDs should be identical
        assert result1 is not None
        assert result2 is not None
        assert result1["id"] == result2["id"]
        assert result1["id"].startswith("workday:") or ":" in result1["id"]  # Should have portal:hash format

    @pytest.mark.asyncio
    async def test_extract_job_from_container_no_title_returns_none(self):
        """Test that missing title returns None (existing behavior preserved)."""
        page = AsyncMock()
        container = AsyncMock()

        # No title element
        container.query_selector = AsyncMock(return_value=None)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TechCorp",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_job_from_container_no_url_still_generates_id(self):
        """Test that missing URL doesn't prevent ID generation (fallback path works)."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Data Scientist")

        location_elem = AsyncMock()
        location_elem.text_content = AsyncMock(return_value="New York")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "location":
                return location_elem
            elif selector == "link":
                return None  # No URL
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="DataCorp",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="",
        )

        # Should still have an ID
        assert result is not None
        assert result["id"] is not None
        assert ":" in result["id"]  # Should have portal:hash format
        assert result["url"] == ""  # URL should be empty string

    @pytest.mark.asyncio
    async def test_extract_job_from_container_defaults(self):
        """Test that description, requirements, salary_* default to None."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Frontend Developer")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            return None  # All other fields None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="WebCorp",
            selectors={"title": "title"},
            base_url="",
        )

        assert result is not None
        assert result["description"] is None
        assert result["requirements"] is None
        assert result["salary_min"] is None
        assert result["salary_max"] is None
        assert result["posted_date"] is None

    @pytest.mark.asyncio
    async def test_extract_job_from_container_posted_date_extraction(self):
        """Test that posted_date is extracted and parsed from posted_on selector."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Backend Developer")

        posted_on_elem = AsyncMock()
        posted_on_elem.text_content = AsyncMock(return_value="Posted 5 Days Ago")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "posted_on":
                return posted_on_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TechCorp",
            selectors={"title": "title", "posted_on": "posted_on"},
            base_url="",
        )

        assert result is not None
        assert result["posted_date"] is not None
        # Verify it's a valid ISO date string
        assert len(result["posted_date"]) == 10  # YYYY-MM-DD format
        assert result["posted_date"].count("-") == 2

    @pytest.mark.asyncio
    async def test_extract_job_from_container_posted_date_none_when_no_selector(self):
        """Test that posted_date is None when posted_on selector is not provided."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="DevOps Engineer")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="CloudCorp",
            selectors={"title": "title"},  # No posted_on selector
            base_url="",
        )

        assert result is not None
        assert result["posted_date"] is None

    @pytest.mark.asyncio
    async def test_extract_job_from_container_posted_date_unparseable_text(self):
        """Test that posted_date is None for unparseable posted_on text."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="QA Engineer")

        posted_on_elem = AsyncMock()
        posted_on_elem.text_content = AsyncMock(return_value="Some random text")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "posted_on":
                return posted_on_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TestCorp",
            selectors={"title": "title", "posted_on": "posted_on"},
            base_url="",
        )

        assert result is not None
        assert result["posted_date"] is None

    @pytest.mark.asyncio
    async def test_extract_job_from_container_status_default(self):
        """Test that status defaults to 'pending_review'."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="DevOps Engineer")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="CloudCorp",
            selectors={"title": "title"},
            base_url="",
        )

        assert result is not None
        assert result["status"] == "pending_review"

    @pytest.mark.asyncio
    async def test_extract_job_from_container_crawled_at_format(self):
        """Test that crawled_at is in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.mmmmmm)."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="QA Engineer")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="TestCorp",
            selectors={"title": "title"},
            base_url="",
        )

        assert result is not None
        crawled_at = result["crawled_at"]
        # Should be parseable as ISO format
        dt = datetime.fromisoformat(crawled_at)
        assert dt is not None
        # Should not have timezone suffix (naive UTC)
        assert not crawled_at.endswith("+00:00")
        assert not crawled_at.endswith("Z")

    @pytest.mark.asyncio
    async def test_extract_job_from_container_field_types(self):
        """Test that returned fields have correct types."""
        page = AsyncMock()
        container = AsyncMock()

        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="ML Engineer")

        location_elem = AsyncMock()
        location_elem.text_content = AsyncMock(return_value="Boston")

        link_elem = AsyncMock()
        link_elem.get_attribute = AsyncMock(return_value="/jobs/789")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "location":
                return location_elem
            elif selector == "link":
                return link_elem
            return None

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        result = await extract_job_from_container(
            page=page,
            container=container,
            company_name="AILabs",
            selectors={"title": "title", "location": "location", "link": "link"},
            base_url="https://careers.ai.com/",
        )

        assert result is not None
        assert isinstance(result["id"], str)
        assert isinstance(result["title"], str)
        assert isinstance(result["company"], str)
        assert isinstance(result["location"], str)
        assert isinstance(result["url"], str)
        assert result["description"] is None
        assert result["requirements"] is None
        assert isinstance(result["crawled_at"], str)
        assert isinstance(result["status"], str)


class TestCrawlCompanyJobs:
    """Test suite for crawl_company_jobs function."""

    @pytest.mark.asyncio
    async def test_crawl_company_jobs_uses_display_name(self):
        """Test that company display name from config is used in extracted jobs."""
        browser = AsyncMock()
        page = AsyncMock()
        browser.new_page = AsyncMock(return_value=page)

        # Mock container
        container = AsyncMock()
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Backend Developer")

        location_elem = AsyncMock()
        location_elem.text_content = AsyncMock(return_value="Remote")

        async def query_selector_side_effect(selector):
            if selector == "title":
                return title_elem
            elif selector == "location":
                return location_elem
            elif selector == "job_container":
                return [container]
            return None

        page.query_selector = AsyncMock(side_effect=query_selector_side_effect)
        page.query_selector_all = AsyncMock(return_value=[container])
        page.wait_for_selector = AsyncMock()
        page.wait_for_timeout = AsyncMock()
        page.close = AsyncMock()

        container.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        company_config = {
            "enabled": True,
            "name": "Carbon Robotics",  # Display name
            "url": "https://example.com/careers",
            "selectors": {
                "job_container": "job_container",
                "title": "title",
                "location": "location",
                "link": None,
            },
            "crawler": {},
        }

        with patch("src.poc.tweak.crawl_list.retry_goto", new_callable=AsyncMock) as mock_retry:
            mock_retry.return_value = True
            jobs = await crawl_company_jobs(
                browser=browser,
                company_key="CarbonRobotics",  # Key
                company_config=company_config,
                timeout_ms=30000,
            )

        assert len(jobs) > 0
        # Company field should be display name, not key
        assert jobs[0]["company"] == "Carbon Robotics"

    @pytest.mark.asyncio
    async def test_crawl_company_jobs_skip_disabled(self):
        """Test that disabled companies are skipped."""
        browser = AsyncMock()

        company_config = {
            "enabled": False,  # Disabled
            "name": "Test Company",
            "url": "https://example.com/careers",
        }

        jobs = await crawl_company_jobs(
            browser=browser,
            company_key="TestCompany",
            company_config=company_config,
            timeout_ms=30000,
        )

        assert jobs == []
        browser.new_page.assert_not_called()

    @pytest.mark.asyncio
    async def test_crawl_company_jobs_no_url(self):
        """Test that companies without URL are skipped."""
        browser = AsyncMock()

        company_config = {
            "enabled": True,
            "name": "Test Company",
            # No URL
        }

        jobs = await crawl_company_jobs(
            browser=browser,
            company_key="TestCompany",
            company_config=company_config,
            timeout_ms=30000,
        )

        assert jobs == []
        browser.new_page.assert_not_called()
