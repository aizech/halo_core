"""Tests for the tool registry pattern."""

import logging
from unittest.mock import MagicMock


from services.tool_registry import (
    TOOL_BUILDERS,
    TOOL_METADATA,
    build_tool,
    build_tools_from_registry,
    register_tool,
)


class TestToolRegistry:
    """Tests for tool registry functions."""

    def test_tool_builders_is_dict(self):
        """TOOL_BUILDERS should be a dictionary."""
        assert isinstance(TOOL_BUILDERS, dict)

    def test_tool_metadata_is_dict(self):
        """TOOL_METADATA should be a dictionary."""
        assert isinstance(TOOL_METADATA, dict)

    def test_registered_tools_have_metadata(self):
        """Each registered tool should have corresponding metadata."""
        for tool_id in TOOL_BUILDERS:
            assert tool_id in TOOL_METADATA, f"Missing metadata for {tool_id}"

    def test_metadata_has_required_fields(self):
        """Tool metadata should have required fields."""
        required_fields = {"display_name", "description", "category"}
        for tool_id, meta in TOOL_METADATA.items():
            for field in required_fields:
                assert hasattr(
                    meta, field
                ), f"Missing '{field}' in metadata for {tool_id}"

    def test_register_tool_adds_builder(self):
        """register_tool should add a builder function."""
        from services.tool_registry import ToolMetadata

        def dummy_builder(settings, **kwargs):
            return "dummy_tool"

        meta = ToolMetadata(
            id="test_tool", display_name="Test", description="Test", category="test"
        )
        register_tool("test_tool", dummy_builder, meta)

        assert "test_tool" in TOOL_BUILDERS
        assert "test_tool" in TOOL_METADATA

        # Clean up
        TOOL_BUILDERS.pop("test_tool", None)
        TOOL_METADATA.pop("test_tool", None)

    def test_build_tool_returns_none_for_unknown(self):
        """build_tool should return None for unknown tool IDs."""
        result = build_tool("unknown_tool_xyz", {})
        assert result is None

    def test_build_tool_calls_builder(self):
        """build_tool should call the registered builder."""
        from services.tool_registry import ToolMetadata

        mock_tool = MagicMock()

        def mock_builder(settings, openai_api_key):
            return mock_tool

        meta = ToolMetadata(
            id="mock_tool", display_name="Mock", description="Mock", category="test"
        )
        register_tool("mock_tool", mock_builder, meta)

        result = build_tool("mock_tool", {})

        assert result is mock_tool

        # Clean up
        TOOL_BUILDERS.pop("mock_tool", None)
        TOOL_METADATA.pop("mock_tool", None)

    def test_build_tools_from_registry_returns_list(self):
        """build_tools_from_registry should return a list."""
        logger = logging.getLogger("test")
        result = build_tools_from_registry([], {}, logger=logger)
        assert isinstance(result, list)

    def test_build_tools_from_registry_filters_unknown(self):
        """build_tools_from_registry should filter unknown tools."""
        logger = logging.getLogger("test")
        result = build_tools_from_registry(["unknown_xyz"], {}, logger=logger)
        assert result == []

    def test_build_tools_from_registry_handles_settings(self):
        """build_tools_from_registry should pass settings to builders."""
        from services.tool_registry import ToolMetadata

        mock_tool = MagicMock()
        captured_settings = {}

        def capturing_builder(settings, openai_api_key):
            captured_settings.update(settings)
            return mock_tool

        meta = ToolMetadata(
            id="capturing_tool",
            display_name="Capturing",
            description="Test",
            category="test",
        )
        register_tool("capturing_tool", capturing_builder, meta)

        result = build_tools_from_registry(
            ["capturing_tool"],
            {"capturing_tool": {"test_key": "test_value"}},
        )

        assert result  # Use the result
        assert "test_key" in captured_settings

        # Clean up
        TOOL_BUILDERS.pop("capturing_tool", None)
        TOOL_METADATA.pop("capturing_tool", None)

    def test_pubmed_tool_registered(self):
        """PubMed tool should be registered."""
        assert "pubmed" in TOOL_BUILDERS
        assert "pubmed" in TOOL_METADATA

    def test_wikipedia_tool_registered(self):
        """Wikipedia tool should be registered."""
        assert "wikipedia" in TOOL_BUILDERS
        assert "wikipedia" in TOOL_METADATA

    def test_calculator_tool_registered(self):
        """Calculator tool should be registered."""
        assert "calculator" in TOOL_BUILDERS
        assert "calculator" in TOOL_METADATA

    def test_image_tool_registered(self):
        """Image tool should be registered."""
        assert "image" in TOOL_BUILDERS
        assert "image" in TOOL_METADATA


class TestToolRegistryCategories:
    """Tests for tool category organization."""

    def test_medical_tools_category(self):
        """Medical-related tools should have appropriate category."""
        medical_tools = ["pubmed"]
        for tool_id in medical_tools:
            if tool_id in TOOL_METADATA:
                meta = TOOL_METADATA[tool_id]
                # Should have some category defined
                assert hasattr(meta, "category")

    def test_search_tools_category(self):
        """Search tools should have appropriate category."""
        search_tools = ["duckduckgo", "websearch", "wikipedia"]
        for tool_id in search_tools:
            if tool_id in TOOL_METADATA:
                meta = TOOL_METADATA[tool_id]
                assert hasattr(meta, "category")
