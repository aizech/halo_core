"""Tests for services/retrieval.py — get_source_chunk_texts and source_id safety guard."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services import retrieval


class TestGetSourceChunkTexts:
    """Coverage for get_source_chunk_texts with/without source_id filter."""

    def _make_mock_db(self, rows):
        mock_db = MagicMock()
        mock_db.table_names.return_value = ["sources"]
        mock_table = MagicMock()
        mock_search = MagicMock()
        mock_search.where.return_value = mock_search
        mock_search.limit.return_value = mock_search
        mock_search.to_list.return_value = rows
        mock_table.search.return_value = mock_search
        mock_db.open_table.return_value = mock_table
        return mock_db, mock_table

    def test_returns_empty_when_no_source_id_or_title(self) -> None:
        result = retrieval.get_source_chunk_texts("", "")
        assert result == []

    def test_returns_empty_when_table_missing(self) -> None:
        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_db.table_names.return_value = []
            mock_connect.return_value = mock_db
            result = retrieval.get_source_chunk_texts("abc123" * 5 + "ab", "")
            assert result == []

    def test_rejects_unsafe_source_id(self, caplog) -> None:
        import logging

        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_db.table_names.return_value = ["sources"]
            mock_connect.return_value = mock_db
            with caplog.at_level(logging.WARNING, logger="services.retrieval"):
                result = retrieval.get_source_chunk_texts("../../etc/passwd", "")
        assert result == []
        assert "unsafe source_id rejected" in caplog.text

    def test_rejects_unsafe_source_id_with_quotes(self, caplog) -> None:
        import logging

        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_db.table_names.return_value = ["sources"]
            mock_connect.return_value = mock_db
            with caplog.at_level(logging.WARNING, logger="services.retrieval"):
                result = retrieval.get_source_chunk_texts("' OR '1'='1", "")
        assert result == []
        assert "unsafe source_id rejected" in caplog.text

    def test_accepts_valid_uuid_hex_source_id(self) -> None:
        from uuid import uuid4

        valid_id = uuid4().hex  # 32 lowercase hex chars
        rows = [
            {
                "payload": '{"content": "chunk text", "meta_data": {}}',
                "meta": {"source_id": valid_id, "title": "Doc"},
                "text": "chunk text",
            }
        ]
        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db, mock_table = self._make_mock_db(rows)
            mock_connect.return_value = mock_db
            with patch.object(
                retrieval, "_ensure_sources_table", return_value=mock_table
            ):
                result = retrieval.get_source_chunk_texts(valid_id, "")
        assert isinstance(result, list)

    def test_falls_back_to_title_when_no_source_id(self) -> None:
        rows = [
            {
                "payload": '{"content": "by title", "meta_data": {}}',
                "meta": {"title": "MyDoc"},
                "text": "by title",
            }
        ]
        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db, mock_table = self._make_mock_db(rows)
            mock_connect.return_value = mock_db
            with patch.object(
                retrieval, "_ensure_sources_table", return_value=mock_table
            ):
                result = retrieval.get_source_chunk_texts("", "MyDoc")
        assert isinstance(result, list)


class TestIsSafeSourceId:
    """Unit tests for the _is_safe_source_id guard."""

    def test_valid_uuid_hex(self) -> None:
        from uuid import uuid4

        assert retrieval._is_safe_source_id(uuid4().hex) is True

    def test_rejects_path_traversal(self) -> None:
        assert retrieval._is_safe_source_id("../../etc/passwd") is False

    def test_rejects_sql_injection(self) -> None:
        assert retrieval._is_safe_source_id("' OR '1'='1") is False

    def test_rejects_uppercase_hex(self) -> None:
        assert retrieval._is_safe_source_id("A" * 32) is False

    def test_rejects_wrong_length(self) -> None:
        assert retrieval._is_safe_source_id("abc123") is False

    def test_rejects_empty(self) -> None:
        assert retrieval._is_safe_source_id("") is False
