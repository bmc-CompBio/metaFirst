#!/usr/bin/env python3
"""
metaFirst Ingest Helper

A watchdog-based tool that watches folders on user machines and registers
new raw data references + sample metadata in the supervisor DB via API.
"""

import os
import sys
import time
import re
import hashlib
from pathlib import Path
from typing import Any

import yaml
import httpx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent


class SupervisorClient:
    """Client for interacting with the metaFirst Supervisor API."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._token: str | None = None
        self._client = httpx.Client(timeout=30.0)

    def _get_token(self) -> str:
        """Get or refresh JWT token."""
        if self._token:
            return self._token

        response = self._client.post(
            f"{self.base_url}/api/auth/login",
            data={"username": self.username, "password": self.password},
        )
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")

        self._token = response.json()["access_token"]
        return self._token

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the API."""
        headers = {"Authorization": f"Bearer {self._get_token()}"}

        response = self._client.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            json=json,
            params=params,
        )

        # Handle token expiration
        if response.status_code == 401:
            self._token = None
            headers = {"Authorization": f"Bearer {self._get_token()}"}
            response = self._client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=json,
                params=params,
            )

        if response.status_code >= 400:
            raise Exception(f"API error {response.status_code}: {response.text}")

        return response.json()

    def get_samples(self, project_id: int) -> list[dict]:
        """Get samples for a project."""
        return self._request("GET", f"/api/projects/{project_id}/samples")

    def create_sample(self, project_id: int, sample_identifier: str) -> dict:
        """Create a new sample."""
        return self._request(
            "POST",
            f"/api/projects/{project_id}/samples",
            json={"sample_identifier": sample_identifier},
        )

    def find_or_create_sample(self, project_id: int, sample_identifier: str) -> dict:
        """Find existing sample or create a new one."""
        samples = self.get_samples(project_id)
        for sample in samples:
            if sample["sample_identifier"] == sample_identifier:
                return sample
        return self.create_sample(project_id, sample_identifier)

    def set_sample_field(
        self, sample_id: int, field_key: str, value: Any
    ) -> dict:
        """Set a field value for a sample."""
        return self._request(
            "PUT",
            f"/api/samples/{sample_id}/fields/{field_key}",
            json={"value": value},
        )

    def get_rdmp(self, project_id: int) -> dict | None:
        """Get the current RDMP for a project."""
        try:
            return self._request("GET", f"/api/rdmp/projects/{project_id}/rdmp")
        except Exception:
            return None

    def create_raw_data_item(
        self,
        project_id: int,
        storage_root_id: int,
        relative_path: str,
        sample_id: int | None = None,
        file_size_bytes: int | None = None,
        file_hash_sha256: str | None = None,
    ) -> dict:
        """Register a new raw data item."""
        data = {
            "storage_root_id": storage_root_id,
            "relative_path": relative_path,
        }
        if sample_id:
            data["sample_id"] = sample_id
        if file_size_bytes:
            data["file_size_bytes"] = file_size_bytes
        if file_hash_sha256:
            data["file_hash_sha256"] = file_hash_sha256

        return self._request("POST", f"/api/projects/{project_id}/raw-data", json=data)

    def close(self):
        """Close the HTTP client."""
        self._client.close()


class WatcherConfig:
    """Configuration for a single watched folder."""

    def __init__(
        self,
        watch_path: str,
        project_id: int,
        storage_root_id: int,
        base_path_for_relative: str | None = None,
        sample_identifier_pattern: str | None = None,
    ):
        self.watch_path = Path(watch_path).resolve()
        self.project_id = project_id
        self.storage_root_id = storage_root_id
        self.base_path_for_relative = (
            Path(base_path_for_relative).resolve()
            if base_path_for_relative
            else self.watch_path
        )
        self.sample_identifier_pattern = sample_identifier_pattern

    def compute_relative_path(self, file_path: Path) -> str:
        """Compute the relative path from base_path_for_relative."""
        return str(file_path.relative_to(self.base_path_for_relative))

    def extract_sample_identifier(self, file_path: Path) -> str | None:
        """Extract sample identifier from filename using pattern, or return None."""
        if not self.sample_identifier_pattern:
            return None

        filename = file_path.name
        match = re.match(self.sample_identifier_pattern, filename)
        if match:
            # Return first capturing group if exists, otherwise full match
            groups = match.groups()
            return groups[0] if groups else match.group(0)
        return None


def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def prompt_for_value(prompt: str, default: str | None = None) -> str | None:
    """Prompt user for a value with optional default."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        user_input = input(f"{prompt} (press Enter to skip): ").strip()
        return user_input if user_input else None


class IngestEventHandler(FileSystemEventHandler):
    """Handler for file creation events."""

    def __init__(
        self,
        client: SupervisorClient,
        watcher_config: WatcherConfig,
        rdmp_fields: list[dict] | None = None,
        max_field_prompts: int = 3,
        compute_hash: bool = False,
    ):
        super().__init__()
        self.client = client
        self.config = watcher_config
        self.rdmp_fields = rdmp_fields or []
        self.max_field_prompts = max_field_prompts
        self.compute_hash = compute_hash
        self.processed_files: set[str] = set()

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()

        # Skip if already processed
        if str(file_path) in self.processed_files:
            return

        # Wait a moment for file to be fully written
        time.sleep(0.5)

        # Skip if file doesn't exist anymore (e.g., temp files)
        if not file_path.exists():
            return

        self.processed_files.add(str(file_path))

        try:
            self._process_file(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")

    def _process_file(self, file_path: Path):
        """Process a newly created file."""
        print(f"\n[NEW FILE] {file_path}")

        # Compute relative path
        try:
            relative_path = self.config.compute_relative_path(file_path)
        except ValueError as e:
            print(f"  [SKIP] Cannot compute relative path: {e}")
            return

        print(f"  Relative path: {relative_path}")

        # Extract or prompt for sample identifier
        sample_identifier = self.config.extract_sample_identifier(file_path)
        if sample_identifier:
            print(f"  Auto-detected sample identifier: {sample_identifier}")
            confirm = input("  Confirm or enter new identifier (Enter to accept): ").strip()
            if confirm:
                sample_identifier = confirm
        else:
            sample_identifier = prompt_for_value("  Sample identifier")

        # Find or create sample if identifier provided
        sample_id = None
        if sample_identifier:
            try:
                sample = self.client.find_or_create_sample(
                    self.config.project_id, sample_identifier
                )
                sample_id = sample["id"]
                print(f"  Linked to sample: {sample_identifier} (ID: {sample_id})")
            except Exception as e:
                print(f"  [WARN] Could not create/find sample: {e}")

        # Get file metadata
        file_size = file_path.stat().st_size
        file_hash = compute_file_hash(file_path) if self.compute_hash else None

        # Register raw data item
        try:
            raw_data_item = self.client.create_raw_data_item(
                project_id=self.config.project_id,
                storage_root_id=self.config.storage_root_id,
                relative_path=relative_path,
                sample_id=sample_id,
                file_size_bytes=file_size,
                file_hash_sha256=file_hash,
            )
            print(f"  [OK] Registered raw data item (ID: {raw_data_item['id']})")
        except Exception as e:
            print(f"  [ERROR] Failed to register raw data: {e}")
            return

        # Prompt for RDMP fields (limited to max_field_prompts)
        if sample_id and self.rdmp_fields:
            required_fields = [
                f for f in self.rdmp_fields
                if f.get("required", False)
            ][:self.max_field_prompts]

            if required_fields:
                print(f"  Set up to {len(required_fields)} required fields (press Enter to skip):")

            for field in required_fields:
                field_key = field["key"]
                field_type = field.get("type", "string")
                allowed_values = field.get("allowed_values", [])

                if allowed_values:
                    print(f"    Allowed values for {field_key}: {', '.join(allowed_values)}")

                value = prompt_for_value(f"    {field_key} ({field_type})")

                if value:
                    # Convert value based on type
                    if field_type == "number":
                        try:
                            value = float(value)
                        except ValueError:
                            print(f"    [WARN] Invalid number, skipping field")
                            continue

                    try:
                        self.client.set_sample_field(sample_id, field_key, value)
                        print(f"    [OK] Set {field_key} = {value}")
                    except Exception as e:
                        print(f"    [WARN] Could not set field: {e}")


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_watcher(config_path: str):
    """Run the folder watcher based on configuration."""
    config = load_config(config_path)

    # Initialize client
    client = SupervisorClient(
        base_url=config["supervisor_url"],
        username=config["username"],
        password=config["password"],
    )

    # Test connection
    try:
        client._get_token()
        print(f"[OK] Connected to supervisor at {config['supervisor_url']}")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        sys.exit(1)

    # Set up observers for each watcher
    observer = Observer()
    handlers = []

    for watcher_cfg in config.get("watchers", []):
        watcher_config = WatcherConfig(
            watch_path=watcher_cfg["watch_path"],
            project_id=watcher_cfg["project_id"],
            storage_root_id=watcher_cfg["storage_root_id"],
            base_path_for_relative=watcher_cfg.get("base_path_for_relative"),
            sample_identifier_pattern=watcher_cfg.get("sample_identifier_pattern"),
        )

        # Get RDMP fields for field prompting
        rdmp = client.get_rdmp(watcher_config.project_id)
        rdmp_fields = rdmp.get("rdmp_json", {}).get("fields", []) if rdmp else []

        handler = IngestEventHandler(
            client=client,
            watcher_config=watcher_config,
            rdmp_fields=rdmp_fields,
            max_field_prompts=config.get("max_field_prompts", 3),
            compute_hash=config.get("compute_hash", False),
        )
        handlers.append(handler)

        # Schedule observer
        if not watcher_config.watch_path.exists():
            print(f"[WARN] Watch path does not exist: {watcher_config.watch_path}")
            continue

        observer.schedule(handler, str(watcher_config.watch_path), recursive=True)
        print(
            f"[WATCH] {watcher_config.watch_path} -> "
            f"Project {watcher_config.project_id}, "
            f"StorageRoot {watcher_config.storage_root_id}"
        )

    # Start observer
    observer.start()
    print("\n[READY] Watching for new files. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        observer.stop()

    observer.join()
    client.close()
    print("[DONE] Watcher stopped.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python metafirst_ingest.py <config.yaml>")
        print("\nExample config.yaml:")
        print("""
supervisor_url: http://localhost:8000
username: alice
password: demo123
max_field_prompts: 3
compute_hash: false
watchers:
  - watch_path: /path/to/data/folder
    project_id: 1
    storage_root_id: 1
    base_path_for_relative: /path/to/data
    sample_identifier_pattern: "^([A-Z]+-\\d+)"
""")
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    run_watcher(config_path)


if __name__ == "__main__":
    main()
