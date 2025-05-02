"""
API utilities for Linear API.

This module provides utility functions for making API calls to Linear.
"""

import os
from typing import Dict, Any, Optional

import requests


def call_linear_api(query: str | Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Call the Linear API with the provided query.

    Args:
        query: The GraphQL query or mutation to execute
        api_key: Optional API key. If not provided, the LINEAR_API_KEY environment
                variable will be used.

    Returns:
        The API response data

    Raises:
        ValueError: If no API key is provided and LINEAR_API_KEY environment variable
                  is not set, or if the API call fails
    """
    api_key = api_key or os.getenv("LINEAR_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key provided. Either pass api_key parameter or set LINEAR_API_KEY environment variable."
        )

    # Define the GraphQL endpoint
    endpoint = "https://api.linear.app/graphql"

    # Set headers for authentication and content type
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    # Make the API call
    response = requests.post(endpoint, json=query, headers=headers)

    # Handle errors
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_message = f"Error calling Linear API: {response.status_code}"
        if response.content:
            error_message += f": {response.content.decode('utf-8')}"
        raise ValueError(error_message)

    # Parse the response
    json_response = response.json()

    # Check for GraphQL errors
    if "errors" in json_response:
        errors = json_response["errors"]
        error_message = "\n".join([error.get("message", "Unknown error") for error in errors])
        raise ValueError(f"GraphQL errors: {error_message}")

    # Return the data
    if "data" in json_response:
        return json_response["data"]

    return {}
