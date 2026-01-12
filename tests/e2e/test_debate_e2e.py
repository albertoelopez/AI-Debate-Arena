#!/usr/bin/env python3
"""
End-to-End Tests with Playwright
"This is the part where you run away and I am still in my Danger Zone!" - Ralph Wiggum

Run with: pytest tests/e2e/ --headed (to see browser)
"""

import pytest
import asyncio
import subprocess
import time
import os
import sys
from pathlib import Path

# Playwright imports
try:
    from playwright.sync_api import Page, expect, sync_playwright
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install")


# Skip all tests if playwright not available
pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright not installed. Run: pip install playwright && playwright install"
)


class TestRalphWiggumE2E:
    """
    End-to-End tests for AI Debate Arena
    "I'm a unitard!" - Ralph Wiggum
    """

    SERVER_URL = "http://localhost:8080"
    server_process = None

    @classmethod
    def setup_class(cls):
        """Start the debate server before tests - Me fail tests? That's unpossible!"""
        project_root = Path(__file__).parent.parent.parent
        main_py = project_root / "main.py"

        if main_py.exists():
            # Start server in background
            cls.server_process = subprocess.Popen(
                [sys.executable, str(main_py)],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait for server to start
            time.sleep(3)
            print(f"🚀 Server started with PID {cls.server_process.pid}")

    @classmethod
    def teardown_class(cls):
        """Stop the server after tests - Sleep! That's where I'm a Viking!"""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("🛑 Server stopped")

    def test_homepage_loads_hi_super_nintendo(self, page: Page):
        """Test homepage loads correctly - Hi, Super Nintendo Chalmers!"""
        page.goto(self.SERVER_URL)

        # Check title
        expect(page).to_have_title("AI Debate Arena")

        # Check header exists
        header = page.locator("h1")
        expect(header).to_contain_text("AI Debate Arena")

        # Take screenshot for the yearbook
        page.screenshot(path="tests/e2e/screenshots/homepage_ralph.png")

    def test_debate_topic_input_my_cats_breath(self, page: Page):
        """Test debate topic input - My cat's breath smells like cat food!"""
        page.goto(self.SERVER_URL)

        # Find topic input
        topic_input = page.locator("#debate-topic")
        expect(topic_input).to_be_visible()

        # Clear and type new topic
        topic_input.clear()
        topic_input.fill("Should cats eat people food?")

        # Verify input
        expect(topic_input).to_have_value("Should cats eat people food?")

    def test_round_selector_i_bent_my_wookie(self, page: Page):
        """Test round selector - I bent my Wookie!"""
        page.goto(self.SERVER_URL)

        # Find round selector
        rounds_select = page.locator("#max-rounds")
        expect(rounds_select).to_be_visible()

        # Select different option
        rounds_select.select_option("4")

        # Verify selection
        expect(rounds_select).to_have_value("4")

    def test_create_debate_button_go_banana(self, page: Page):
        """Test create debate button - Go banana!"""
        page.goto(self.SERVER_URL)

        # Find create button
        create_btn = page.locator("#create-debate")
        expect(create_btn).to_be_visible()
        expect(create_btn).to_have_text("Create Debate")
        expect(create_btn).to_be_enabled()

    def test_start_button_initially_disabled_im_in_danger(self, page: Page):
        """Test start button is disabled initially - I'm in danger!"""
        page.goto(self.SERVER_URL)

        # Start button should be disabled before debate creation
        start_btn = page.locator("#start-debate")
        expect(start_btn).to_be_disabled()

    def test_connection_status_shown_learnding(self, page: Page):
        """Test connection status indicator - I'm learnding!"""
        page.goto(self.SERVER_URL)

        # Wait for WebSocket connection
        page.wait_for_timeout(2000)

        # Check connection status element
        status = page.locator("#connection-status")
        expect(status).to_be_visible()

    def test_full_debate_flow_unpossible(self, page: Page):
        """Test complete debate flow - Me fail English? That's unpossible!"""
        page.goto(self.SERVER_URL)

        # 1. Enter topic
        topic_input = page.locator("#debate-topic")
        topic_input.clear()
        topic_input.fill("Should homework be replaced with video games?")

        # 2. Select rounds
        page.locator("#max-rounds").select_option("2")

        # 3. Click create
        page.locator("#create-debate").click()

        # 4. Wait for arena to appear
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # 5. Check topic is displayed
        topic_display = page.locator("#debate-topic-display")
        expect(topic_display).to_contain_text("Should homework be replaced")

        # 6. Start button should now be enabled
        start_btn = page.locator("#start-debate")
        expect(start_btn).to_be_enabled()

        # Screenshot the arena
        page.screenshot(path="tests/e2e/screenshots/debate_arena_ralph.png")

    def test_agent_panels_visible_choo_choo(self, page: Page):
        """Test agent panels are visible after creation - I choo-choo-choose you!"""
        page.goto(self.SERVER_URL)

        # Create a debate
        page.locator("#debate-topic").fill("Should trains give valentines?")
        page.locator("#create-debate").click()
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # Check both agent panels
        pro_panel = page.locator(".agent-pro")
        con_panel = page.locator(".agent-con")

        expect(pro_panel).to_be_visible()
        expect(con_panel).to_be_visible()

        # Check agent names
        expect(pro_panel).to_contain_text("Dr. Advocate")
        expect(con_panel).to_contain_text("Prof. Challenger")

    def test_vs_divider_viking(self, page: Page):
        """Test VS divider appears - Sleep! That's where I'm a Viking!"""
        page.goto(self.SERVER_URL)

        # Create debate
        page.locator("#debate-topic").fill("Are Vikings better than pirates?")
        page.locator("#create-debate").click()
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # Check VS divider
        vs = page.locator(".vs-divider")
        expect(vs).to_be_visible()
        expect(vs).to_contain_text("VS")

    def test_transcript_container_burning(self, page: Page):
        """Test transcript container exists - It tastes like burning!"""
        page.goto(self.SERVER_URL)

        # Create debate
        page.locator("#debate-topic").fill("Is fire hot or cold?")
        page.locator("#create-debate").click()
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # Check transcript container
        transcript = page.locator(".transcript-container")
        expect(transcript).to_be_visible()

        # Check header
        expect(page.locator(".transcript-header")).to_contain_text("Transcript")

    def test_volume_control_nose_goblins(self, page: Page):
        """Test volume control - Ew, nose goblins!"""
        page.goto(self.SERVER_URL)

        # Create debate
        page.locator("#create-debate").click()
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # Find volume slider
        volume_slider = page.locator("#volume-slider")
        expect(volume_slider).to_be_visible()

        # Check initial value
        expect(volume_slider).to_have_value("80")

    def test_stop_button_purple_berries(self, page: Page):
        """Test stop button exists - I eated the purple berries!"""
        page.goto(self.SERVER_URL)

        # Create debate
        page.locator("#create-debate").click()
        page.wait_for_selector("#debate-arena", state="visible", timeout=10000)

        # Stop button should exist but be disabled until debate starts
        stop_btn = page.locator("#stop-debate")
        expect(stop_btn).to_be_visible()
        expect(stop_btn).to_be_disabled()

    def test_api_health_endpoint_sandbox(self, page: Page):
        """Test health API endpoint - That's my sandbox!"""
        # Direct API test
        response = page.request.get(f"{self.SERVER_URL}/health")

        assert response.ok
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_debates" in data

    def test_responsive_design_furniture(self, page: Page):
        """Test responsive design - Look! I'm a Furniture!"""
        page.goto(self.SERVER_URL)

        # Test mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)

        # Should still be usable
        expect(page.locator("#debate-topic")).to_be_visible()
        expect(page.locator("#create-debate")).to_be_visible()

        page.screenshot(path="tests/e2e/screenshots/mobile_ralph.png")

        # Test tablet viewport
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(500)

        page.screenshot(path="tests/e2e/screenshots/tablet_ralph.png")


class TestRalphDebateExecution:
    """
    Tests for actual debate execution
    "Miss Hoover, I glued my head to my shoulder!" - Ralph
    """

    SERVER_URL = "http://localhost:8080"

    def test_start_and_watch_debate_glued(self, page: Page):
        """Test starting and watching a debate - I glued my head to my shoulder!"""
        page.goto(self.SERVER_URL)

        # Wait for page to fully load and WebSocket to connect
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Screenshot initial state
        page.screenshot(path="tests/e2e/screenshots/01_initial_ralph.png")

        # Fill in debate topic
        topic_input = page.locator("#debate-topic")
        topic_input.clear()
        topic_input.fill("Should glue be edible?")

        # Select rounds
        page.locator("#max-rounds").select_option("2")

        # Screenshot before create
        page.screenshot(path="tests/e2e/screenshots/02_before_create_ralph.png")

        # Click create and wait for response
        with page.expect_response(lambda r: "/api/debate/create" in r.url) as response_info:
            page.locator("#create-debate").click()

        response = response_info.value
        print(f"Create debate response: {response.status}")

        # Wait for arena to be visible (checking CSS display property)
        page.wait_for_function(
            """() => {
                const arena = document.getElementById('debate-arena');
                return arena && window.getComputedStyle(arena).display !== 'none';
            }""",
            timeout=15000
        )

        # Screenshot after arena visible
        page.screenshot(path="tests/e2e/screenshots/03_arena_visible_ralph.png")

        # Wait for start button to be enabled
        page.wait_for_function(
            "document.querySelector('#start-debate') && !document.querySelector('#start-debate').disabled",
            timeout=10000
        )

        # Use JavaScript to click (bypasses visibility check)
        page.evaluate("document.querySelector('#start-debate').click()")

        # Screenshot after starting
        page.screenshot(path="tests/e2e/screenshots/04_debate_started_ralph.png")

        # Wait for transcript entries with generous timeout for LLM
        try:
            page.wait_for_selector(".turn-entry", timeout=90000)

            turns = page.locator(".turn-entry")
            count = turns.count()
            print(f"Found {count} transcript entries")
            assert count >= 1, "Expected at least 1 transcript entry"

            # Final screenshot
            page.screenshot(path="tests/e2e/screenshots/05_debate_complete_ralph.png")

        except Exception as e:
            page.screenshot(path="tests/e2e/screenshots/99_error_ralph.png")
            # Print page content for debugging
            print(f"Page URL: {page.url}")
            print(f"Error: {e}")
            raise


# Ralph Wiggum E2E Test Quotes
RALPH_E2E_QUOTES = [
    "I'm a unitard!",
    "When I grow up, I'm going to Bovine University!",
    "I found a moon rock in my nose!",
    "My parents won't let me use scissors!",
    "Oh boy, sleep! That's where I'm a Viking!",
    "Bushes are nice 'cause they don't have prickers... unless they do. This one did. Ouch!",
    "Daddy, I'm scared. Too scared to wet my pants!",
    "The doctor said I wouldn't have so many nose bleeds if I kept my finger outta there.",
]


@pytest.fixture(scope="function")
def page():
    """Playwright page fixture - I'm Idaho!"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()


# Create screenshots directory
screenshots_dir = Path(__file__).parent / "screenshots"
screenshots_dir.mkdir(exist_ok=True)


if __name__ == "__main__":
    import random
    print(f"\n🎭 Running E2E Tests... {random.choice(RALPH_E2E_QUOTES)}\n")
    pytest.main([__file__, "-v", "--tb=short", "-x"])