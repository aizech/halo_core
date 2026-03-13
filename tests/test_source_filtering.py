"""Tests for source-filtered RAG retrieval."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestQuerySimilarSourceFiltering:
    """Tests for source_ids filtering in query_similar."""

    def test_query_similar_accepts_source_ids_parameter(self) -> None:
        """query_similar accepts source_ids parameter without error."""
        from services import retrieval

        # Mock the database connection to return empty
        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_db.table_names.return_value = []
            mock_connect.return_value = mock_db

            # Should not raise
            result = retrieval.query_similar("test query", source_ids=["id1", "id2"])
            assert result == []

    def test_query_similar_filters_by_source_ids(self) -> None:
        """query_similar filters results to only include chunks from specified sources."""
        from services import retrieval

        # Mock the database and table
        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_table = MagicMock()
            mock_db.table_names.return_value = ["sources"]
            mock_connect.return_value = mock_db

            # Mock table search to return results from multiple sources
            mock_search = MagicMock()
            mock_search.metric.return_value = mock_search
            mock_search.limit.return_value = mock_search
            mock_search.to_list.return_value = [
                {
                    "payload": '{"content": "content from source1", "meta_data": {"source_id": "source1"}}',
                    "meta": {"title": "Source 1", "source_id": "source1"},
                    "text": "content from source1",
                    "_distance": 0.1,
                },
                {
                    "payload": '{"content": "content from source2", "meta_data": {"source_id": "source2"}}',
                    "meta": {"title": "Source 2", "source_id": "source2"},
                    "text": "content from source2",
                    "_distance": 0.2,
                },
                {
                    "payload": '{"content": "content from source3", "meta_data": {"source_id": "source3"}}',
                    "meta": {"title": "Source 3", "source_id": "source3"},
                    "text": "content from source3",
                    "_distance": 0.3,
                },
            ]
            mock_table.search.return_value = mock_search

            with patch.object(
                retrieval, "_ensure_sources_table", return_value=mock_table
            ):
                with patch.object(retrieval, "_embed", return_value=[0.1] * 1536):
                    # Filter to only source1 and source2
                    result = retrieval.query_similar(
                        "test query",
                        source_ids=["source1", "source2"],
                    )

            # Should only return chunks from source1 and source2
            assert len(result) == 2
            source_ids_in_result = [
                r["meta"].get("source_id")
                for r in result
                if isinstance(r["meta"], dict)
            ]
            assert "source1" in source_ids_in_result
            assert "source2" in source_ids_in_result
            assert "source3" not in source_ids_in_result

    def test_query_similar_returns_all_when_no_filter(self) -> None:
        """query_similar returns all results when source_ids is None."""
        from services import retrieval

        with patch.object(retrieval, "_connect_db") as mock_connect:
            mock_db = MagicMock()
            mock_table = MagicMock()
            mock_db.table_names.return_value = ["sources"]
            mock_connect.return_value = mock_db

            mock_search = MagicMock()
            mock_search.metric.return_value = mock_search
            mock_search.limit.return_value = mock_search
            mock_search.to_list.return_value = [
                {
                    "payload": '{"content": "content1", "meta_data": {"source_id": "s1"}}',
                    "meta": {"source_id": "s1"},
                    "text": "content1",
                    "_distance": 0.1,
                },
                {
                    "payload": '{"content": "content2", "meta_data": {"source_id": "s2"}}',
                    "meta": {"source_id": "s2"},
                    "text": "content2",
                    "_distance": 0.2,
                },
            ]
            mock_table.search.return_value = mock_search

            with patch.object(
                retrieval, "_ensure_sources_table", return_value=mock_table
            ):
                with patch.object(retrieval, "_embed", return_value=[0.1] * 1536):
                    result = retrieval.query_similar("test query", source_ids=None)

            # Should return all results
            assert len(result) == 2


class TestChatTurnInputSourceIds:
    """Tests for source_ids in ChatTurnInput."""

    def test_chat_turn_input_has_source_ids_field(self) -> None:
        """ChatTurnInput has source_ids field."""
        from services.chat_runtime import ChatTurnInput

        turn = ChatTurnInput(
            prompt="test",
            sources=["Source A"],
            source_ids=["id_a", "id_b"],
        )

        assert turn.source_ids == ["id_a", "id_b"]

    def test_chat_turn_input_source_ids_defaults_to_empty_list(self) -> None:
        """ChatTurnInput source_ids defaults to empty list."""
        from services.chat_runtime import ChatTurnInput

        turn = ChatTurnInput(prompt="test")

        assert turn.source_ids == []

    def test_build_chat_payload_passes_source_ids_to_query_similar(self) -> None:
        """build_chat_payload passes source_ids to query_similar."""
        from services import chat_runtime

        turn = chat_runtime.ChatTurnInput(
            prompt="test query",
            sources=["Source A"],
            source_ids=["id_a"],
        )

        with patch.object(chat_runtime.retrieval, "query_similar") as mock_query:
            mock_query.return_value = []
            with patch.object(chat_runtime.agents, "build_chat_payload") as mock_build:
                mock_build.return_value = "payload"

                chat_runtime.build_chat_payload(turn)

            # Verify query_similar was called with source_ids
            mock_query.assert_called_once()
            call_kwargs = mock_query.call_args
            assert call_kwargs[0][0] == "test query"
            assert call_kwargs[1].get("source_ids") == [
                "id_a"
            ] or call_kwargs.kwargs.get("source_ids") == ["id_a"]
