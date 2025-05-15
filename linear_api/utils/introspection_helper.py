"""
GraphQL introspection helper.

Utility for introspecting GraphQL schema to determine available fields.
"""


def introspect_type(client, type_name):
    """
    Introspect a type in the GraphQL schema.

    Args:
        client: A LinearClient instance
        type_name: The name of the GraphQL type to introspect

    Returns:
        Dict containing information about the type's fields
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

    response = client.execute_graphql(introspection_query, {"typeName": type_name})

    # Return empty result for errors
    if not response or "__type" not in response:
        print(f"Error introspecting type '{type_name}'")
        return {}

    return response["__type"]


def get_field_names(client, type_name):
    """
    Get field names for a GraphQL type.

    Args:
        client: A LinearClient instance
        type_name: The name of the GraphQL type

    Returns:
        List of field names available for the type
    """
    type_info = introspect_type(client, type_name)

    if not type_info or "fields" not in type_info:
        return []

    return [field["name"] for field in type_info["fields"]]


def print_type_fields(client, type_name):
    """
    Print available fields for a GraphQL type.

    Args:
        client: A LinearClient instance
        type_name: The name of the GraphQL type
    """
    type_info = introspect_type(client, type_name)

    if not type_info or "fields" not in type_info:
        print(f"No fields found for type '{type_name}'")
        return

    print(f"\nFields for {type_name}:")
    print("-" * 40)

    for field in type_info["fields"]:
        field_type = field.get("type", {})
        type_name = field_type.get("name") or field_type.get("ofType", {}).get("name", "unknown")
        print(f"- {field['name']}: {type_name}")
        if field.get("description"):
            print(f"  Description: {field['description']}")