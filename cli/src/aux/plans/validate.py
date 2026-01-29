"""Plan validation utilities."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from aux.plans.schemas import DiffPlan, FindPlan, GrepPlan, LsPlan, ScanPlan

T = TypeVar("T", bound=BaseModel)

PLAN_TYPES: dict[str, type[BaseModel]] = {
    "grep": GrepPlan,
    "find": FindPlan,
    "diff": DiffPlan,
    "ls": LsPlan,
    "scan": ScanPlan,
}


def parse_plan(plan_json: str, plan_type: type[T]) -> T:
    """Parse and validate a JSON plan string.

    Args:
        plan_json: JSON string containing plan data
        plan_type: Pydantic model class to validate against

    Returns:
        Validated plan instance

    Raises:
        ValueError: If JSON is invalid or validation fails
    """
    try:
        data = json.loads(plan_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    return validate_plan(data, plan_type)


def validate_plan(data: dict, plan_type: type[T]) -> T:
    """Validate plan data against a schema.

    Args:
        data: Dictionary containing plan data
        plan_type: Pydantic model class to validate against

    Returns:
        Validated plan instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return plan_type.model_validate(data)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"  {loc}: {msg}")
        raise ValueError(f"Plan validation failed:\n" + "\n".join(errors)) from e


def get_schema(command: str) -> dict:
    """Get JSON schema for a command's plan.

    Args:
        command: Command name (grep, find, diff, ls, scan)

    Returns:
        JSON schema dictionary

    Raises:
        ValueError: If command is unknown
    """
    plan_type = PLAN_TYPES.get(command)
    if plan_type is None:
        raise ValueError(f"Unknown command: {command}")

    return plan_type.model_json_schema()
