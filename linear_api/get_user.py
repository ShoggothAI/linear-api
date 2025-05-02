from .call_linear_api import call_linear_api
from .domain import LinearUser

def fetch_linear_user(user_id: str, api_key: str) -> LinearUser:
    """
    Fetches a Linear user by ID and returns a validated Pydantic model with all available fields
    """
    query = """
    query GetUser($userId: String!) {
        user(id: $userId) {
            # Basic fields
            id
            createdAt
            updatedAt
            archivedAt
            name
            displayName
            email
            avatarUrl

            # Additional scalar fields
            active
            admin
            app
            avatarBackgroundColor
            calendarHash
            createdIssueCount
            description
            disableReason
            guest
            initials
            inviteHash
            isMe
            lastSeen
            statusEmoji
            statusLabel
            statusUntilAt
            timezone
            url

            # Basic information about complex objects
            organization {
                id
                name
            }

            # For connection types, we'll just get the basic structure
            # without fetching all nodes to keep the query efficient
            # We're not fetching these complex fields for now to keep the query simple
            # and avoid potential errors with the GraphQL schema
        }
    }
    """

    variables = {"userId": user_id}

    response = call_linear_api({"query": query, "variables": variables})

    raw_data = response["user"]

    return LinearUser(**raw_data)


def get_user_email_map() -> dict[str, str]:
    """
    Returns a dictionary mapping all user IDs to their emails using Linear's GraphQL API.
    """
    query = """
    query {
        users {
            nodes {
                id
                email
            }
        }
    }
    """

    response = call_linear_api({"query": query})

    users = response["users"]["nodes"]
    return {user["id"]: user["email"] for user in users}


