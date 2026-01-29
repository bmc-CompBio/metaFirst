#!/usr/bin/env python3
"""CLI tool to push sample metadata from supervisor to discovery index.

Usage:
    export SUPERVISOR_URL=http://localhost:8000
    export SUPERVISOR_USERNAME=alice
    export SUPERVISOR_PASSWORD=demo123
    export DISCOVERY_URL=http://localhost:8000/api/discovery
    export DISCOVERY_API_KEY=your-secret-key

    python tools/discovery_push.py --project-id 1 --visibility PUBLIC
"""

import argparse
import json
import os
import sys

import httpx


def get_env_or_exit(key: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(key)
    if not value:
        print(f"Error: {key} environment variable not set", file=sys.stderr)
        sys.exit(1)
    return value


def get_supervisor_token(base_url: str, username: str, password: str) -> str:
    """Authenticate with supervisor and get token."""
    response = httpx.post(
        f"{base_url}/api/auth/login",
        data={"username": username, "password": password},
    )
    if response.status_code != 200:
        print(f"Failed to authenticate: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()["access_token"]


def get_samples_with_fields(base_url: str, token: str, project_id: int) -> list[dict]:
    """Get all samples with their field values for a project."""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{base_url}/api/projects/{project_id}/samples",
        headers=headers,
    )
    if response.status_code != 200:
        print(f"Failed to get samples: {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def push_to_discovery(
    discovery_url: str,
    api_key: str,
    origin: str,
    records: list[dict],
) -> dict:
    """Push records to the discovery index."""
    headers = {"Authorization": f"ApiKey {api_key}"}
    payload = {"origin": origin, "records": records}

    response = httpx.post(
        f"{discovery_url}/push",
        headers=headers,
        json=payload,
        timeout=30.0,
    )

    if response.status_code != 200:
        print(f"Failed to push to discovery: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Push sample metadata from supervisor to discovery index"
    )
    parser.add_argument(
        "--project-id",
        type=int,
        required=True,
        help="Project ID to export samples from",
    )
    parser.add_argument(
        "--visibility",
        choices=["PUBLIC", "REGISTERED", "PRIVATE"],
        default="PUBLIC",
        help="Visibility level for pushed records (default: PUBLIC)",
    )
    parser.add_argument(
        "--origin",
        default=None,
        help="Origin identifier (default: SUPERVISOR_URL hostname)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be pushed without actually pushing",
    )
    args = parser.parse_args()

    # Get configuration from environment
    supervisor_url = get_env_or_exit("SUPERVISOR_URL").rstrip("/")
    username = get_env_or_exit("SUPERVISOR_USERNAME")
    password = get_env_or_exit("SUPERVISOR_PASSWORD")
    discovery_url = get_env_or_exit("DISCOVERY_URL").rstrip("/")
    api_key = get_env_or_exit("DISCOVERY_API_KEY")

    # Determine origin
    origin = args.origin
    if not origin:
        from urllib.parse import urlparse
        origin = urlparse(supervisor_url).netloc

    print(f"Supervisor: {supervisor_url}")
    print(f"Discovery:  {discovery_url}")
    print(f"Origin:     {origin}")
    print(f"Project:    {args.project_id}")
    print(f"Visibility: {args.visibility}")
    print()

    # Authenticate with supervisor
    print("Authenticating with supervisor...")
    token = get_supervisor_token(supervisor_url, username, password)

    # Get samples
    print(f"Fetching samples for project {args.project_id}...")
    samples = get_samples_with_fields(supervisor_url, token, args.project_id)
    print(f"Found {len(samples)} samples")

    if not samples:
        print("No samples to push")
        return

    # Build push records
    records = []
    for sample in samples:
        # Build metadata from field values
        metadata = {
            "sample_identifier": sample.get("sample_identifier"),
        }

        # Add field values if present
        field_values = sample.get("field_values", [])
        for fv in field_values:
            field_key = fv.get("field_key")
            value = fv.get("value_json") or fv.get("value_text")
            if field_key and value is not None:
                metadata[field_key] = value

        records.append({
            "origin_project_id": args.project_id,
            "origin_sample_id": sample["id"],
            "sample_identifier": sample.get("sample_identifier"),
            "visibility": args.visibility,
            "metadata": metadata,
        })

    if args.dry_run:
        print("\n--- DRY RUN: Would push the following records ---")
        print(json.dumps({"origin": origin, "records": records}, indent=2))
        return

    # Push to discovery
    print(f"Pushing {len(records)} records to discovery index...")
    result = push_to_discovery(discovery_url, api_key, origin, records)

    print(f"Upserted: {result['upserted']}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
