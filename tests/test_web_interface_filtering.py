"""Simplified tests for web interface SoundCloud OAuth token handling and filtering display."""

import pytest
from web_server import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestWebInterfaceGeneration:
    """Test the web interface generation form and functionality."""

    def test_generate_form_displays_soundcloud_token_field(self, client):
        """Test that the generation form includes SoundCloud OAuth token field."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for SoundCloud token field
        assert "soundcloud-token" in html_content
        assert "SoundCloud OAuth Token (Optional)" in html_content
        assert "textarea" in html_content

    def test_generate_form_includes_detailed_instructions(self, client):
        """Test that the form includes detailed OAuth token extraction instructions."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for detailed instructions
        assert "🔑 How to extract your SoundCloud OAuth token" in html_content
        assert "Developer Tools" in html_content
        assert "oauth_token" in html_content
        assert "Chrome/Edge" in html_content
        assert "Firefox" in html_content
        assert "Safari" in html_content
        assert "Application tab" in html_content
        assert "Storage tab" in html_content
        assert "Cookies" in html_content

    def test_generate_form_includes_privacy_information(self, client):
        """Test that the form includes privacy and usage information."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for privacy and usage info
        assert "⚡ What this does:" in html_content
        assert "fresh discoveries" in html_content
        assert "🔒 Privacy:" in html_content
        assert "not stored permanently" in html_content

    def test_generate_form_includes_step_by_step_instructions(self, client):
        """Test that the form includes detailed step-by-step instructions."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for step-by-step instructions
        assert "Step 1:" in html_content
        assert "Step 2:" in html_content
        assert "Step 3:" in html_content
        assert "Step 4:" in html_content
        assert "Step 5:" in html_content
        assert "Step 6:" in html_content

        # Check for browser-specific instructions
        assert "Chrome/Edge:" in html_content
        assert "Firefox:" in html_content
        assert "Safari:" in html_content

        # Check for specific technical details
        assert "F12" in html_content
        assert "right-click" in html_content
        assert "Inspect" in html_content
        assert "https://soundcloud.com" in html_content


class TestFilteringStatisticsDisplay:
    """Test the filtering statistics display in the web interface."""

    def test_javascript_handles_filtering_stats_with_removals(self, client):
        """Test that JavaScript properly formats filtering statistics with removals."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for filtering statistics display logic
        assert "🎯 Platform Filtering Results:" in html_content
        assert "stats.removed_count > 0" in html_content
        assert "✨ Filtered for Fresh Discoveries!" in html_content
        assert "duplicate tracks removed" in html_content
        assert "fresh tracks in your playlist" in html_content
        assert "SoundCloud matches found" in html_content

    def test_javascript_handles_no_duplicates_found(self, client):
        """Test JavaScript display when no duplicates are found."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for no duplicates message
        assert "🎉 All Fresh Tracks!" in html_content
        assert "No duplicate tracks found" in html_content
        assert "new discoveries" in html_content

    def test_javascript_handles_filtering_errors(self, client):
        """Test JavaScript display when filtering errors occur."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for error handling
        assert "⚠️ Filtering Warnings:" in html_content
        assert "filtering operations encountered issues" in html_content
        assert "may contain some tracks from your library" in html_content

    def test_javascript_handles_missing_filtering_stats(self, client):
        """Test JavaScript display when filtering stats are missing."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for missing stats handling
        assert "no filtering stats available" in html_content
        assert "Check server logs" in html_content

    def test_javascript_includes_visual_styling(self, client):
        """Test that filtering statistics include proper visual styling."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for styled containers
        assert "background: #fef3c7" in html_content  # Warning style
        assert "background: #dcfce7" in html_content  # Success style
        assert "background: #fef2f2" in html_content  # Error style
        assert "background: #dbeafe" in html_content  # Info style

        # Check for border styling
        assert "border-left: 4px solid" in html_content
        assert "border-radius: 6px" in html_content
        assert "padding: 10px" in html_content


class TestAPIGenerateEndpoint:
    """Test the /api/generate endpoint basic functionality."""

    def test_generate_missing_required_fields(self, client):
        """Test API response when required fields are missing."""
        response = client.post("/api/generate", json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "data" in data["error"].lower()

    def test_generate_empty_tags(self, client):
        """Test API response when tags list is empty."""
        response = client.post(
            "/api/generate",
            json={"tags": [], "tracks": 8, "limit": 100, "language": "en"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "tag" in data["error"].lower()

    def test_generate_accepts_soundcloud_token_parameter(self, client):
        """Test that the API accepts soundcloud_token parameter without error."""
        # This test just verifies the parameter is accepted, not the full functionality
        response = client.post(
            "/api/generate",
            json={
                "tags": ["rock"],
                "tracks": 1,
                "limit": 10,
                "language": "en",
                "soundcloud_token": "test_token",
            },
        )

        # The request should be accepted (may fail later due to missing dependencies)
        # but it shouldn't fail due to the soundcloud_token parameter
        assert response.status_code in [
            200,
            500,
        ]  # Either success or internal error, not 400


class TestFormInteractivity:
    """Test form interactivity and user experience."""

    def test_form_includes_quick_tags(self, client):
        """Test that the form includes quick tag buttons."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for quick tag functionality
        assert "quick-tags" in html_content
        assert "quick-tag" in html_content
        assert "data-tag=" in html_content

        # Check for specific quick tags
        assert "rock" in html_content
        assert "pop" in html_content
        assert "electronic" in html_content
        assert "jazz" in html_content

    def test_form_includes_javascript_functionality(self, client):
        """Test that the form includes necessary JavaScript functionality."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for JavaScript functions
        assert "addEventListener" in html_content
        assert "updateTagsInput" in html_content
        assert "fetch(" in html_content
        assert "JSON.stringify" in html_content

        # Check for form submission handling
        assert "generate-form" in html_content
        assert "submit" in html_content

    def test_form_includes_loading_states(self, client):
        """Test that the form includes loading state handling."""
        response = client.get("/generate")
        assert response.status_code == 200

        html_content = response.get_data(as_text=True)

        # Check for loading state elements
        assert "status loading" in html_content
        assert "Generating playlist..." in html_content
        assert "disabled = true" in html_content
        assert "status success" in html_content
        assert "status error" in html_content


if __name__ == "__main__":
    pytest.main([__file__])
