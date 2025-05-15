"""
Tests for model completeness.

This module tests that core domain models include all fields from the Linear GraphQL schema.
"""

import pytest
import os

from linear_api import LinearClient
from linear_api.domain import (
    LinearIssue,
    LinearUser,
    LinearProject,
    LinearTeam,
)


@pytest.fixture
def client():
    """Create a LinearClient instance for testing."""
    # Get the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create and return the client
    return LinearClient(api_key=api_key)


def test_model_completeness(client):
    """Test that core models include all fields from the Linear GraphQL schema."""
    # List of models to check
    models = [
        LinearIssue,
        LinearUser,
        LinearProject,
        LinearTeam,
    ]

    # Model names for better error reporting
    model_names = {
        "LinearIssue": "Issue",
        "LinearUser": "User",
        "LinearProject": "Project",
        "LinearTeam": "Team",
    }

    # Test each model
    for model_class in models:
        # Validate the model against the schema
        result = client.validate_schema(model_class)

        # Get model completeness
        completeness = result.get("completeness", 0) * 100

        # Get missing fields for better error reporting
        missing_fields = result.get("missing_in_model", [])

        # Get model name for better error message
        model_name = model_class.__name__
        graphql_type = model_names.get(model_name, model_class.linear_class_name)

        # Debug print when there are missing fields
        if missing_fields:
            print(f"\nMissing fields in {model_name} (GraphQL Type: {graphql_type}):")
            for field in missing_fields:
                print(f"  - {field}")

        # Check all property getters on the model
        property_fields = []
        for attr_name in dir(model_class):
            if isinstance(getattr(model_class, attr_name), property):
                property_fields.append(attr_name)

        # Known missing fields that are handled by property getters
        known_missing = set(model_class.known_missing_fields if hasattr(model_class, "known_missing_fields") else [])

        # Property fields should match known_missing_fields
        for field in property_fields:
            if field not in known_missing and not field.startswith('_'):
                print(f"Warning: Property {field} is not listed in known_missing_fields for {model_name}")

        # Assert that all fields in known_missing_fields have corresponding property getters
        for field in known_missing:
            assert field in property_fields, f"Field {field} is in known_missing_fields but has no property getter in {model_name}"

        # Calculate adjusted completeness considering property getters
        adjusted_missing_count = len([f for f in missing_fields if f not in property_fields])
        if adjusted_missing_count == 0:
            adjusted_completeness = 100.0
        else:
            total_fields = len(result.get("common_fields", [])) + len(missing_fields)
            adjusted_completeness = ((total_fields - adjusted_missing_count) / total_fields) * 100

        # Assert the adjusted completeness is 100%
        assert adjusted_completeness == 100.0, (
                f"{model_name} (GraphQL Type: {graphql_type}) model is not 100% complete. " +
                f"Adjusted completeness: {adjusted_completeness:.1f}%. " +
                f"Missing fields: {[f for f in missing_fields if f not in property_fields]}"
        )

        # Also check original completeness
        assert completeness == 100.0, (
                f"{model_name} (GraphQL Type: {graphql_type}) model is not 100% complete. " +
                f"Completeness: {completeness:.1f}%. Missing fields: {missing_fields}"
        )


def test_model_has_necessary_soft_deletion_fields(client):
    """Test that models have all necessary soft deletion fields."""
    # List of models to check
    models = [
        LinearIssue,
        LinearUser,
        LinearProject,
        LinearTeam,
    ]

    # Soft deletion fields that should be present
    soft_delete_fields = ["archivedAt"]

    # Additional fields based on model type
    issue_fields = ["trashed", "canceledAt", "completedAt", "autoArchivedAt"]
    project_fields = ["trashed", "canceledAt", "completedAt", "autoArchivedAt"]

    # Test each model
    for model_class in models:
        # Validate the model against the schema
        result = client.validate_schema(model_class)

        # Get common fields
        common_fields = set(result.get("common_fields", []))

        # Check required soft deletion fields for all models
        for field in soft_delete_fields:
            assert field in common_fields, f"{field} should be present in {model_class.__name__}"

        # Check additional fields based on model type
        if model_class is LinearIssue:
            for field in issue_fields:
                assert field in common_fields, f"{field} should be present in LinearIssue"

        if model_class is LinearProject:
            for field in project_fields:
                assert field in common_fields, f"{field} should be present in LinearProject"
