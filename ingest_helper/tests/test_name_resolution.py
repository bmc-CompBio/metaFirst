"""Unit tests for name-based resolution of project and storage root configs."""

import pytest
from unittest.mock import MagicMock, patch

# Import the module under test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from metafirst_ingest import (
    resolve_watcher_config,
    resolve_all_watchers,
    ResolvedWatcherConfig,
    SupervisorClient,
)


class TestResolveWatcherConfig:
    """Tests for resolve_watcher_config function."""

    def test_numeric_ids_only(self):
        """Test that numeric IDs work without any API calls."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_id": 2,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert error is None
        assert result is not None
        assert result.project_id == 1
        assert result.storage_root_id == 2
        assert result.resolved_by_name is False
        # No API calls should have been made
        mock_client.get_projects.assert_not_called()
        mock_client.get_storage_roots.assert_not_called()

    def test_project_name_resolves_to_single_match(self):
        """Test successful resolution of project_name to project_id."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Test Project"},
            {"id": 20, "name": "Other Project"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_name": "Test Project",
            "storage_root_id": 5,
        }

        # Provide empty cache so it fetches
        projects_cache = {"Test Project": {"id": 10, "name": "Test Project"}}

        result, error = resolve_watcher_config(
            watcher_cfg, mock_client, projects_cache=projects_cache
        )

        assert error is None
        assert result is not None
        assert result.project_id == 10
        assert result.project_name == "Test Project"
        assert result.storage_root_id == 5
        assert result.resolved_by_name is True

    def test_project_name_not_found(self):
        """Test that missing project_name returns error."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Other Project"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_name": "Nonexistent Project",
            "storage_root_id": 5,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "not found" in error.lower()
        assert "Nonexistent Project" in error

    def test_project_name_ambiguous(self):
        """Test that multiple matching projects returns ambiguous error."""
        mock_client = MagicMock(spec=SupervisorClient)
        # This shouldn't happen in practice (names are unique), but test defensive handling
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Duplicate Name"},
            {"id": 20, "name": "Duplicate Name"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_name": "Duplicate Name",
            "storage_root_id": 5,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "ambiguous" in error.lower()

    def test_storage_root_name_resolves_to_single_match(self):
        """Test successful resolution of storage_root_name to storage_root_id."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "LOCAL_DATA"},
            {"id": 200, "name": "REMOTE_BACKUP"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_name": "LOCAL_DATA",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert error is None
        assert result is not None
        assert result.project_id == 1
        assert result.storage_root_id == 100
        assert result.storage_root_name == "LOCAL_DATA"
        assert result.resolved_by_name is True
        mock_client.get_storage_roots.assert_called_once_with(1)

    def test_storage_root_name_not_found(self):
        """Test that missing storage_root_name returns error."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "SOME_ROOT"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_name": "MISSING_ROOT",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "not found" in error.lower()
        assert "MISSING_ROOT" in error

    def test_storage_root_name_ambiguous(self):
        """Test that multiple matching storage roots returns ambiguous error."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "Duplicate"},
            {"id": 200, "name": "Duplicate"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_name": "Duplicate",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "ambiguous" in error.lower()

    def test_both_name_resolution(self):
        """Test resolving both project_name and storage_root_name."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "My Project"},
        ]
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "My Storage"},
        ]

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_name": "My Project",
            "storage_root_name": "My Storage",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert error is None
        assert result is not None
        assert result.project_id == 10
        assert result.storage_root_id == 100
        assert result.resolved_by_name is True
        # Storage roots should be fetched for the resolved project ID
        mock_client.get_storage_roots.assert_called_once_with(10)

    def test_numeric_id_takes_precedence_over_name(self):
        """Test that numeric IDs take precedence when both are provided."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 99,  # This should be used
            "project_name": "Some Project",  # This should be ignored
            "storage_root_id": 88,  # This should be used
            "storage_root_name": "Some Root",  # This should be ignored
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert error is None
        assert result is not None
        assert result.project_id == 99
        assert result.storage_root_id == 88
        assert result.resolved_by_name is False
        # No API calls should have been made since numeric IDs take precedence
        mock_client.get_projects.assert_not_called()
        mock_client.get_storage_roots.assert_not_called()

    def test_missing_watch_path(self):
        """Test that missing watch_path returns error."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "project_id": 1,
            "storage_root_id": 2,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "watch_path" in error.lower()

    def test_missing_both_project_id_and_name(self):
        """Test error when neither project_id nor project_name provided."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "watch_path": "/data/folder",
            "storage_root_id": 2,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "project_id" in error.lower() or "project_name" in error.lower()

    def test_missing_both_storage_root_id_and_name(self):
        """Test error when neither storage_root_id nor storage_root_name provided."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "storage_root_id" in error.lower() or "storage_root_name" in error.lower()

    def test_api_error_on_projects_fetch(self):
        """Test that API errors during project fetch are handled gracefully."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.side_effect = Exception("API error 500: Internal Server Error")

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_name": "Test Project",
            "storage_root_id": 5,
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "api error" in error.lower()

    def test_api_error_on_storage_roots_fetch(self):
        """Test that API errors during storage roots fetch are handled gracefully."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_storage_roots.side_effect = Exception("API error 500: Internal Server Error")

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_name": "My Storage",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert result is None
        assert error is not None
        assert "api error" in error.lower()

    def test_optional_fields_preserved(self):
        """Test that optional fields like base_path_for_relative are preserved."""
        mock_client = MagicMock(spec=SupervisorClient)

        watcher_cfg = {
            "watch_path": "/data/folder",
            "project_id": 1,
            "storage_root_id": 2,
            "base_path_for_relative": "/data",
            "sample_identifier_pattern": "^([A-Z]+-\\d+)",
        }

        result, error = resolve_watcher_config(watcher_cfg, mock_client)

        assert error is None
        assert result is not None
        assert result.base_path_for_relative == "/data"
        assert result.sample_identifier_pattern == "^([A-Z]+-\\d+)"


class TestResolveAllWatchers:
    """Tests for resolve_all_watchers function."""

    def test_all_watchers_resolve_successfully(self):
        """Test that all valid watchers are resolved."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Project A"},
            {"id": 20, "name": "Project B"},
        ]
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "Storage A"},
        ]

        watchers_cfg = [
            {"watch_path": "/path/a", "project_id": 1, "storage_root_id": 2},
            {"watch_path": "/path/b", "project_name": "Project A", "storage_root_name": "Storage A"},
        ]

        resolved, failed = resolve_all_watchers(watchers_cfg, mock_client)

        assert len(resolved) == 2
        assert len(failed) == 0

    def test_some_watchers_fail(self):
        """Test that failed watchers are collected separately."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Valid Project"},
        ]

        watchers_cfg = [
            {"watch_path": "/path/a", "project_id": 1, "storage_root_id": 2},  # Valid
            {"watch_path": "/path/b", "project_name": "Missing Project", "storage_root_id": 2},  # Invalid
            {"watch_path": "/path/c"},  # Invalid - missing project and storage root
        ]

        resolved, failed = resolve_all_watchers(watchers_cfg, mock_client)

        assert len(resolved) == 1
        assert len(failed) == 2
        # Check that failed entries contain the config and error message
        assert failed[0][0]["watch_path"] == "/path/b"
        assert "not found" in failed[0][1].lower()
        assert failed[1][0]["watch_path"] == "/path/c"

    def test_empty_watchers_list(self):
        """Test handling of empty watchers list."""
        mock_client = MagicMock(spec=SupervisorClient)

        resolved, failed = resolve_all_watchers([], mock_client)

        assert len(resolved) == 0
        assert len(failed) == 0

    def test_projects_cache_is_reused(self):
        """Test that projects are fetched only once and cached."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_projects.return_value = [
            {"id": 10, "name": "Project A"},
            {"id": 20, "name": "Project B"},
        ]
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "Storage"},
        ]

        watchers_cfg = [
            {"watch_path": "/path/a", "project_name": "Project A", "storage_root_name": "Storage"},
            {"watch_path": "/path/b", "project_name": "Project B", "storage_root_name": "Storage"},
        ]

        resolved, failed = resolve_all_watchers(watchers_cfg, mock_client)

        assert len(resolved) == 2
        assert len(failed) == 0
        # get_projects should only be called once (cached for second watcher)
        assert mock_client.get_projects.call_count == 1

    def test_storage_roots_cache_is_reused_per_project(self):
        """Test that storage roots are cached per project_id."""
        mock_client = MagicMock(spec=SupervisorClient)
        mock_client.get_storage_roots.return_value = [
            {"id": 100, "name": "Storage"},
        ]

        watchers_cfg = [
            {"watch_path": "/path/a", "project_id": 1, "storage_root_name": "Storage"},
            {"watch_path": "/path/b", "project_id": 1, "storage_root_name": "Storage"},
            {"watch_path": "/path/c", "project_id": 2, "storage_root_name": "Storage"},
        ]

        resolved, failed = resolve_all_watchers(watchers_cfg, mock_client)

        assert len(resolved) == 3
        # get_storage_roots should be called twice (once per unique project_id)
        assert mock_client.get_storage_roots.call_count == 2


class TestResolvedWatcherConfig:
    """Tests for ResolvedWatcherConfig dataclass."""

    def test_all_fields_set(self):
        """Test that all fields can be set and retrieved."""
        config = ResolvedWatcherConfig(
            watch_path="/data/folder",
            project_id=1,
            storage_root_id=2,
            project_name="My Project",
            storage_root_name="My Storage",
            base_path_for_relative="/data",
            sample_identifier_pattern="^test",
            resolved_by_name=True,
        )

        assert config.watch_path == "/data/folder"
        assert config.project_id == 1
        assert config.storage_root_id == 2
        assert config.project_name == "My Project"
        assert config.storage_root_name == "My Storage"
        assert config.base_path_for_relative == "/data"
        assert config.sample_identifier_pattern == "^test"
        assert config.resolved_by_name is True

    def test_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        config = ResolvedWatcherConfig(
            watch_path="/data/folder",
            project_id=1,
            storage_root_id=2,
        )

        assert config.project_name is None
        assert config.storage_root_name is None
        assert config.base_path_for_relative is None
        assert config.sample_identifier_pattern is None
        assert config.resolved_by_name is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
