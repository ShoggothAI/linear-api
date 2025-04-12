import os
import requests
from typing import Dict, Any, Optional

def call_linear_api(query: str|Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:

    api_key = api_key or os.getenv("LINEAR_API_KEY")
    assert api_key, "Please set the LINEAR_API_KEY environment variable or pass it as an argument"

    # Define the GraphQL endpoint
    endpoint = "https://api.linear.app/graphql"
    # Set headers for authentication and content type
    headers = {
    "Authorization": api_key or os.getenv("LINEAR_API_KEY"),
    "Content-Type": "application/json"
    }

    response = requests.post(endpoint, json=query, headers=headers)

    response.raise_for_status()
    return response.json()["data"]

