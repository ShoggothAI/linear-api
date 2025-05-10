"""
Utility script for exploring the Linear API schema.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from linear_api import LinearClient
from linear_api.utils.introspection_helper import print_type_fields

def main():
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: Please set LINEAR_API_KEY environment variable")
        sys.exit(1)

    client = LinearClient(api_key=api_key)

    if len(sys.argv) < 2:
        print("Usage: python explore_schema.py <TypeName>")
        print("Example: python explore_schema.py CustomerNeed")
        sys.exit(1)

    type_name = sys.argv[1]

    print_type_fields(client, type_name)

if __name__ == "__main__":
    main()