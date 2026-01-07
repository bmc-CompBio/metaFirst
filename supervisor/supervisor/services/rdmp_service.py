"""RDMP validation and management service."""

from typing import Any
from sqlalchemy.orm import Session

from supervisor.models.rdmp import RDMPVersion
from supervisor.models.sample import Sample


def validate_rdmp_schema(rdmp_json: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate RDMP JSON structure against schema."""
    errors = []

    # Check required top-level keys
    if "roles" not in rdmp_json:
        errors.append("Missing 'roles' key")
    if "fields" not in rdmp_json:
        errors.append("Missing 'fields' key")

    # Validate roles
    if "roles" in rdmp_json:
        roles = rdmp_json["roles"]
        if not isinstance(roles, list) or len(roles) == 0:
            errors.append("'roles' must be a non-empty list")
        else:
            role_names = set()
            for i, role in enumerate(roles):
                if "name" not in role:
                    errors.append(f"Role {i} missing 'name'")
                else:
                    if role["name"] in role_names:
                        errors.append(f"Duplicate role name: {role['name']}")
                    role_names.add(role["name"])

                if "permissions" not in role:
                    errors.append(f"Role {i} missing 'permissions'")
                else:
                    perms = role["permissions"]
                    required_perms = ["can_edit_metadata", "can_edit_paths", "can_create_release", "can_manage_rdmp"]
                    for perm in required_perms:
                        if perm not in perms:
                            errors.append(f"Role '{role.get('name', i)}' missing permission '{perm}'")

    # Validate fields
    if "fields" in rdmp_json:
        fields = rdmp_json["fields"]
        if not isinstance(fields, list) or len(fields) == 0:
            errors.append("'fields' must be a non-empty list")
        else:
            field_keys = set()
            for i, field in enumerate(fields):
                if "key" not in field:
                    errors.append(f"Field {i} missing 'key'")
                else:
                    if field["key"] in field_keys:
                        errors.append(f"Duplicate field key: {field['key']}")
                    field_keys.add(field["key"])

                if "label" not in field:
                    errors.append(f"Field {i} missing 'label'")

                if "type" not in field:
                    errors.append(f"Field {i} missing 'type'")
                elif field["type"] not in ["string", "number", "date", "categorical"]:
                    errors.append(f"Field '{field.get('key', i)}' has invalid type: {field['type']}")

                if "visibility" in field and field["visibility"] not in ["private", "collaborators", "public_index"]:
                    errors.append(f"Field '{field.get('key', i)}' has invalid visibility: {field['visibility']}")

                # Categorical fields should have allowed_values
                if field.get("type") == "categorical" and "allowed_values" not in field:
                    errors.append(f"Categorical field '{field.get('key', i)}' missing 'allowed_values'")

    return (len(errors) == 0, errors)


def check_sample_completeness(sample: Sample, rdmp: RDMPVersion) -> dict[str, Any]:
    """Check if sample has all required fields."""
    rdmp_json = rdmp.rdmp_json
    required_fields = [f for f in rdmp_json.get("fields", []) if f.get("required", False)]
    existing_field_keys = {fv.field_key for fv in sample.field_values}

    missing = [f["key"] for f in required_fields if f["key"] not in existing_field_keys]

    return {
        "is_complete": len(missing) == 0,
        "missing_fields": missing,
        "total_required": len(required_fields),
        "total_filled": len(existing_field_keys),
    }


def validate_field_value(field_config: dict[str, Any], value: Any) -> tuple[bool, str | None]:
    """Validate a field value against RDMP field definition."""
    field_type = field_config.get("type")

    # Type validation
    if field_type == "number":
        try:
            float(value)
        except (ValueError, TypeError):
            return (False, f"Value must be a number")

    elif field_type == "categorical":
        allowed_values = field_config.get("allowed_values", [])
        if value not in allowed_values:
            return (False, f"Value must be one of: {', '.join(allowed_values)}")

    elif field_type == "date":
        # Basic date format check (can be enhanced)
        if not isinstance(value, str):
            return (False, "Date must be a string")

    return (True, None)


def get_current_rdmp(db: Session, project_id: int) -> RDMPVersion | None:
    """Get the latest RDMP version for a project."""
    return (
        db.query(RDMPVersion)
        .filter(RDMPVersion.project_id == project_id)
        .order_by(RDMPVersion.version_int.desc())
        .first()
    )
