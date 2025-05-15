"""
Schema validator for Linear API domain models.

This module uses GraphQL introspection to check if our domain models are using all available fields
from the Linear API. It helps ensure our models are comprehensive and up-to-date.
"""

import inspect
import os
from typing import Dict, Set, Any, Tuple

from pydantic import BaseModel

from linear_api.domain import (
    LinearIssue,
    LinearUser,
    LinearState,
    LinearLabel,
    LinearProject,
    LinearTeam,
    LinearAttachment,
)
from linear_api.domain.base_domain import LinearModel
from linear_api.utils import call_linear_api


def get_schema_for_type(type_name: str, api_key: str) -> Dict[str, Any]:
    """
    Use GraphQL introspection to get the schema for a specific type.

    Args:
        type_name: The name of the GraphQL type to introspect
        api_key: The Linear API key for authentication

    Returns:
        A dictionary containing the type's fields and their types
    """
    introspection_query = """
    query IntrospectionQuery($typeName: String!) {
      __type(name: $typeName) {
        name
        kind
        description
        fields {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
    """

    response = call_linear_api(
        {"query": introspection_query, "variables": {"typeName": type_name}}, api_key=api_key
    )

    if not response or "__type" not in response:
        raise ValueError(f"Type '{type_name}' not found in the Linear API schema")

    return response["__type"]


def get_model_fields(model_class: type[LinearModel]) -> Set[str]:
    """
    Get all field names from a Pydantic model, including @property methods.

    Args:
        model_class: The Pydantic model class to inspect

    Returns:
        A set of field names
    """
    if not issubclass(model_class, BaseModel):
        raise ValueError(f"{model_class.__name__} is not a Pydantic model")

    # Get all fields from the model
    all_fields = set(model_class.__annotations__.keys())

    # Add property methods
    for name, member in inspect.getmembers(model_class):
        if isinstance(member, property):
            all_fields.add(name)

    # Get fields to exclude from model_config
    excluded_fields = set()
    if hasattr(model_class, "model_config"):
        # In Pydantic v2, model_config is a ConfigDict object
        config = model_class.model_config
        if isinstance(config, dict) and "exclude" in config:
            exclude_config = config["exclude"]
            if isinstance(exclude_config, set):
                excluded_fields = exclude_config
            elif isinstance(exclude_config, dict):
                excluded_fields = set(exclude_config.keys())
            elif hasattr(exclude_config, "__iter__"):
                excluded_fields = set(exclude_config)

    # Return fields that are not excluded
    return all_fields - excluded_fields


def compare_fields(
        model_class: type[LinearModel], api_key: str
) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Compare fields between a Pydantic model and a GraphQL type.

    Args:
        model_class: The Pydantic model class to check
        api_key: The Linear API key for authentication

    Returns:
        A tuple containing:
        - Fields present in both the model and GraphQL type
        - Fields missing from the model but present in GraphQL
        - Fields present in the model but missing from GraphQL
    """
    # Get model fields
    model_fields = get_model_fields(model_class)

    # Get GraphQL type name from the model class
    graphql_type_name = model_class.linear_class_name

    # Get GraphQL type fields
    graphql_schema = get_schema_for_type(graphql_type_name, api_key=api_key)
    graphql_fields = set()

    if graphql_schema and "fields" in graphql_schema:
        for field in graphql_schema["fields"]:
            graphql_fields.add(field["name"])

    # Compare fields
    common_fields = model_fields.intersection(graphql_fields)
    missing_in_model = graphql_fields - model_fields
    extra_in_model = model_fields - graphql_fields

    # Filter out known missing fields
    if hasattr(model_class, "known_missing_fields") and model_class.known_missing_fields:
        missing_in_model = missing_in_model - set(model_class.known_missing_fields)

    # Filter out known extra fields
    if hasattr(model_class, "known_extra_fields") and model_class.known_extra_fields:
        extra_in_model = extra_in_model - set(model_class.known_extra_fields)

    return common_fields, missing_in_model, extra_in_model


def validate_model(model_class: type[LinearModel], api_key: str) -> Dict[str, Any]:
    """
    Validate a Pydantic model against a GraphQL type.

    Args:
        model_class: The Pydantic model class to validate
        api_key: The Linear API key for authentication

    Returns:
        A dictionary containing validation results
    """
    graphql_type_name = model_class.linear_class_name
    try:
        common, missing, extra = compare_fields(model_class, api_key=api_key)

        # Get known missing and extra fields
        known_missing = model_class.known_missing_fields if hasattr(model_class, "known_missing_fields") else []
        known_extra = model_class.known_extra_fields if hasattr(model_class, "known_extra_fields") else []

        return {
            "model_name": model_class.__name__,
            "graphql_type": graphql_type_name,
            "common_fields": sorted(list(common)),
            "missing_in_model": sorted(list(missing)),
            "extra_in_model": sorted(list(extra)),
            "known_missing_fields": sorted(known_missing),
            "known_extra_fields": sorted(known_extra),
            "completeness": (
                len(common) / (len(common) + len(missing) + len(
                    known_missing)) if common or missing or known_missing else 1.0
            ),
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_name": model_class.__name__,
            "graphql_type": graphql_type_name,
        }


def validate_all_models(api_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Validate all domain models against their corresponding GraphQL types.

    Args:
        api_key: The Linear API key for authentication

    Returns:
        A dictionary mapping model names to validation results
    """
    # List of model classes to validate
    models_to_validate = [
        LinearIssue,
        LinearUser,
        LinearState,
        LinearLabel,
        LinearProject,
        LinearTeam,
        LinearAttachment,
    ]

    results = {}

    for model_class in models_to_validate:
        try:
            results[model_class.__name__] = validate_model(
                model_class, api_key=api_key
            )
        except Exception as e:
            results[model_class.__name__] = {
                "error": str(e),
                "model_name": model_class.__name__,
                "graphql_type": model_class.linear_class_name,
            }

    return results


def print_validation_results(results: Dict[str, Dict[str, Any]]) -> None:
    """
    Print validation results in a readable format.

    Args:
        results: The validation results from validate_all_models()
    """
    for model_name, result in results.items():
        print(f"\n{'=' * 80}")
        print(f"Model: {model_name} | GraphQL Type: {result.get('graphql_type')}")
        print(f"{'=' * 80}")

        if "error" in result:
            print(f"Error: {result['error']}")
            continue

        completeness = result.get("completeness", 0) * 100
        print(f"Completeness: {completeness:.1f}%")

        if result.get("missing_in_model"):
            print("\nFields missing from model:")
            for field in result["missing_in_model"]:
                print(f"  - {field}")

        if result.get("known_missing_fields"):
            print("\nKnown missing fields (intentionally excluded):")
            for field in result["known_missing_fields"]:
                print(f"  - {field}")

        if result.get("extra_in_model"):
            print("\nExtra fields in model (not in GraphQL schema):")
            for field in result["extra_in_model"]:
                print(f"  - {field}")

        if result.get("known_extra_fields"):
            print("\nKnown extra fields (intentionally included):")
            for field in result["known_extra_fields"]:
                print(f"  - {field}")

    print("\n")


def get_field_details(graphql_type_name: str, api_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Get detailed information about all fields of a GraphQL type.

    Args:
        graphql_type_name: The name of the GraphQL type to inspect
        api_key: The Linear API key for authentication

    Returns:
        A dictionary mapping field names to their details
    """
    schema = get_schema_for_type(graphql_type_name, api_key=api_key)
    field_details = {}

    if schema and "fields" in schema:
        for field in schema["fields"]:
            field_type = field["type"]
            type_name = field_type.get("name")

            # Handle non-null and list types
            if not type_name and field_type.get("kind") in ["NON_NULL", "LIST"]:
                if "ofType" in field_type and field_type["ofType"]:
                    type_name = field_type["ofType"].get("name")

            field_details[field["name"]] = {
                "type": type_name,
                "kind": field_type.get("kind"),
                "description": field.get("description"),
            }

    return field_details


def suggest_model_improvements(
        model_class: type[LinearModel], api_key: str
) -> str:
    """
    Generate suggestions for improving a model based on missing fields.

    Args:
        model_class: The Pydantic model class to improve
        api_key: The Linear API key for authentication

    Returns:
        A string containing suggested code improvements
    """
    _, missing, _ = compare_fields(model_class, api_key=api_key)

    if not missing:
        return f"# {model_class.__name__} is already complete!"

    graphql_type_name = model_class.linear_class_name
    field_details = get_field_details(graphql_type_name, api_key=api_key)
    suggestions = [f"# Suggested improvements for {model_class.__name__}:"]

    # Get known missing fields to exclude from suggestions
    known_missing = set(model_class.known_missing_fields) if hasattr(model_class, "known_missing_fields") else set()

    # Add a note about known missing fields if there are any
    if known_missing:
        suggestions.append(f"# Note: {len(known_missing)} known missing fields are excluded from suggestions")
        suggestions.append(f"# Known missing fields: {', '.join(sorted(known_missing))}")

    for field in sorted(missing):
        if field in field_details:
            detail = field_details[field]
            field_type = detail.get("type", "Any")

            # Map GraphQL types to Python types
            type_mapping = {
                "String": "str",
                "Int": "int",
                "Float": "float",
                "Boolean": "bool",
                "ID": "str",
                "DateTime": "datetime",
            }

            python_type = type_mapping.get(field_type, field_type)

            # Handle lists and optional fields
            if detail.get("kind") == "LIST":
                python_type = f"List[{python_type}]"

            if detail.get("kind") != "NON_NULL":
                python_type = f"Optional[{python_type}]"
                default = " = None"
            else:
                default = ""

            suggestions.append(f"    {field}: {python_type}{default}")

    return "\n".join(suggestions)


if __name__ == "__main__":
    api_key = os.environ["LINEAR_API_KEY"]
    print("Validating Linear API domain models against GraphQL schema...")
    results = validate_all_models(api_key=api_key)
    print_validation_results(results)

    # Generate improvement suggestions for a specific model
    print("Generating improvement suggestions for LinearProject:")
    suggestions = suggest_model_improvements(LinearProject, api_key=api_key)
    print(suggestions)
