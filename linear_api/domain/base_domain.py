"""
Base domain model for Linear API.

This module defines the base classes and utilities for all domain models.
"""

from typing import Optional, Dict, Any, ClassVar, TypeVar, Generic, List

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class LinearModel(BaseModel):
    """
    Base class for all Linear domain models.

    This adds a class variable `linear_class_name` that indicates
    the corresponding GraphQL type name in the Linear API,
    and excludes this from serialization.
    """

    # Class variable for the GraphQL type name
    linear_class_name: ClassVar[str] = ""
    known_missing_fields: ClassVar[List[str]] = []
    known_extra_fields: ClassVar[List[str]] = []

    _client: Any = PrivateAttr(default=None)
    # Configuration to exclude class variables from serialization
    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating by field name and alias
        exclude={
            "linear_class_name",
            "known_missing_fields",
            "known_extra_fields",
        },  # Exclude class variables from serialization
    )

    def with_client(self, client):
        """
        Sets the client reference for this model.

        Args:
            client: LinearClient instance

        Returns:
            self for call chain
        """
        self._client = client
        return self

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """
        Override model_dump to exclude class variables.

        Args:
            **kwargs: Additional options for model_dump

        Returns:
            A dictionary of the model's fields with class variables excluded
        """
        # Set exclude in kwargs if not already set
        if "exclude" not in kwargs:
            kwargs["exclude"] = set()
        elif isinstance(kwargs["exclude"], set):
            pass  # Already a set, no need to modify
        else:
            kwargs["exclude"] = set(kwargs["exclude"])

        # Add linear_class_name to excluded fields
        kwargs["exclude"].add("linear_class_name")

        # Call parent class's model_dump method
        return super().model_dump(**kwargs)

    @classmethod
    def get_linear_class_name(cls) -> str:
        """
        Get the corresponding Linear API class name.

        Returns:
            The GraphQL type name in the Linear API
        """
        return cls.linear_class_name


# Generic connection type for pagination
T = TypeVar("T")


class Connection(LinearModel, Generic[T]):
    """Generic connection model for paginated results"""

    linear_class_name: ClassVar[str] = "Connection"

    nodes: List[T] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None
