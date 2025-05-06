"""
Tests for the schema validator module.
"""

import pytest
from unittest.mock import patch, MagicMock

from linear_api.schema_validator import compare_fields, validate_model, get_model_fields
from linear_api.domain.base_domain import LinearModel
from pydantic import ConfigDict


class TestModel(LinearModel):
    """Test model for schema validator tests"""
    linear_class_name = "TestType"
    known_missing_fields = ["known_missing_field1", "known_missing_field2"]
    known_extra_fields = ["known_extra_field1", "known_extra_field2"]

    field1: str
    field2: int
    known_extra_field1: str
    known_extra_field2: int
    excluded_field1: str
    excluded_field2: int

    # Configure excluded fields
    model_config = ConfigDict(
        exclude={"excluded_field1", "excluded_field2"}
    )


def test_get_model_fields_excludes_config_fields():
    """Test that get_model_fields excludes fields listed in model_config.exclude"""
    # Call the function
    fields = get_model_fields(TestModel)

    # Verify results
    assert "field1" in fields
    assert "field2" in fields
    assert "known_extra_field1" in fields
    assert "known_extra_field2" in fields
    assert "excluded_field1" not in fields
    assert "excluded_field2" not in fields


@patch("linear_api.schema_validator.get_schema_for_type")
def test_compare_fields_with_known_fields(mock_get_schema):
    """Test that compare_fields ignores known missing and extra fields"""
    # Setup mock
    mock_get_schema.return_value = {
        "fields": [
            {"name": "field1"},
            {"name": "field2"},
            {"name": "graphql_field3"},
            {"name": "graphql_field4"},
            {"name": "known_missing_field1"},
            {"name": "known_missing_field2"},
        ]
    }

    # Call the function
    common, missing, extra = compare_fields(TestModel, api_key="fake_key")

    # Verify results
    assert common == {"field1", "field2"}
    assert missing == {"graphql_field3", "graphql_field4"}  # known_missing_fields should be excluded
    assert "known_extra_field1" not in extra  # known_extra_fields should be excluded
    assert "known_extra_field2" not in extra  # known_extra_fields should be excluded


@patch("linear_api.schema_validator.compare_fields")
def test_validate_model_includes_known_fields(mock_compare_fields):
    """Test that validate_model includes known fields in the results"""
    # Setup mock
    mock_compare_fields.return_value = (
        {"field1", "field2"},  # common
        {"graphql_field3", "graphql_field4"},  # missing
        set()  # extra (known_extra_fields are filtered out by compare_fields)
    )

    # Call the function
    result = validate_model(TestModel, api_key="fake_key")

    # Verify results
    assert result["model_name"] == "TestModel"
    assert result["graphql_type"] == "TestType"
    assert result["common_fields"] == ["field1", "field2"]
    assert result["missing_in_model"] == ["graphql_field3", "graphql_field4"]
    assert result["extra_in_model"] == []
    assert result["known_missing_fields"] == ["known_missing_field1", "known_missing_field2"]
    assert result["known_extra_fields"] == ["known_extra_field1", "known_extra_field2"]

    # Check completeness calculation includes known_missing_fields
    expected_completeness = 2 / (2 + 2 + 2)  # common / (common + missing + known_missing)
    assert result["completeness"] == expected_completeness
