"""
Script for initializing test data in Linear.
Creates labels, cycles, and templates in the "Test" team to ensure test passing.
"""

import os
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from linear_api import LinearClient
from linear_api.domain import LinearPriority


def initialize_test_data():
    """
    Initializes test data in the "Test" team for Linear API testing.
    """
    # Get API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY environment variable is not set")
        return False

    # Create client instance
    client = LinearClient(api_key=api_key)

    # Test team name
    test_team_name = "Test"

    try:
        # Get Test team ID
        team_id = client.teams.get_id_by_name(test_team_name)
        print(f"Found Test team with ID: {team_id}")

        # 1. Create labels
        create_test_labels(client, team_id, test_team_name)

        # 2. Configure cycles
        create_test_cycles(client, team_id, test_team_name)

        # 3. Create templates
        create_test_templates(client, team_id, test_team_name)

        print("✅ Test data initialization completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error initializing test data: {e}")
        return False


def get_existing_labels(client, team_id):
    """Gets the list of existing labels in the team."""
    try:
        # Query to get all team labels
        query = """
       query($teamId: ID!) {
         issueLabels(filter: { team: { id: { eq: $teamId } } }) {
           nodes {
             id
             name
             color
           }
         }
       }
       """

        response = client.execute_graphql(query, {"teamId": team_id})

        if response and "issueLabels" in response and "nodes" in response["issueLabels"]:
            return [label["name"] for label in response["issueLabels"]["nodes"]]
        return []
    except Exception as e:
        print(f"Failed to retrieve existing labels: {e}")
        return []


def create_test_labels(client, team_id, team_name):
    """Creates test labels in the team."""
    # Get existing labels
    existing_label_names = get_existing_labels(client, team_id)
    print(f"Existing labels: {existing_label_names}")

    # If labels already exist, just exit
    if len(existing_label_names) >= 4:
        print(f"✓ Team {team_name} already has enough labels ({len(existing_label_names)} items)")
        return

    # Create missing labels
    label_data = [
        {"name": "Test Bug", "color": "#FF0000"},
        {"name": "Test Feature", "color": "#00FF00"},
        {"name": "Test Enhancement", "color": "#0000FF"},
        {"name": "Test Documentation", "color": "#FFFF00"}
    ]

    for label in label_data:
        # Skip if a label with this name already exists
        if label["name"] in existing_label_names:
            print(f"✓ Label {label['name']} already exists, skipping")
            continue

        # API for creating a label
        mutation = """
       mutation CreateLabel($input: IssueLabelCreateInput!) {
         issueLabelCreate(input: $input) {
           success
           issueLabel {
             id
             name
             color
           }
         }
       }
       """

        variables = {
            "input": {
                "name": label["name"],
                "color": label["color"],
                "teamId": team_id
            }
        }

        try:
            response = client.execute_graphql(mutation, variables)
            if response and "issueLabelCreate" in response and response["issueLabelCreate"]["success"]:
                print(f"✓ Created label: {label['name']} (color: {label['color']})")
            else:
                print(f"✗ Failed to create label: {label['name']}")
        except Exception as e:
            print(f"✗ Error creating label {label['name']}: {e}")


def create_test_cycles(client, team_id, team_name):
    """Creates test cycles in the team."""
    # Check existing cycles
    try:
        # Query to get cycles
        query = """
       query($teamId: ID!) {
         cycles(filter: { team: { id: { eq: $teamId } } }) {
           nodes {
             id
             name
             number
           }
         }
       }
       """

        response = client.execute_graphql(query, {"teamId": team_id})

        if response and "cycles" in response and "nodes" in response["cycles"]:
            existing_cycles = response["cycles"]["nodes"]
            # If cycles already exist, just exit
            if existing_cycles and len(existing_cycles) > 0:
                print(f"✓ Cycles already exist in team {team_name} ({len(existing_cycles)} items)")
                return
    except Exception as e:
        print(f"Failed to retrieve existing cycles: {e}")

    # Current date and time
    now = datetime.now()

    # Create active cycle
    start_date = now - timedelta(days=7)  # started a week ago
    end_date = now + timedelta(days=7)  # ends in a week

    # API for creating a cycle
    mutation = """
   mutation CreateCycle($input: CycleCreateInput!) {
     cycleCreate(input: $input) {
       success
       cycle {
         id
         name
         number
       }
     }
   }
   """

    variables = {
        "input": {
            "teamId": team_id,
            "name": "Test Cycle",
            "startsAt": start_date.isoformat(),
            "endsAt": end_date.isoformat()
        }
    }

    try:
        response = client.execute_graphql(mutation, variables)
        if response and "cycleCreate" in response and response["cycleCreate"]["success"]:
            print(f"✓ Created cycle: Test Cycle ({start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')})")
        else:
            print(f"✗ Failed to create cycle")
    except Exception as e:
        print(f"✗ Error creating cycle: {e}")


def get_existing_templates(client, team_id):
    """Gets the list of existing templates in the team."""
    try:
        # Query to get team templates
        query = """
       query($teamId: String!) {
         team(id: $teamId) {
           id
           templates {
             nodes {
               id
               name
               type
             }
           }
         }
       }
       """

        response = client.execute_graphql(query, {"teamId": team_id})

        if (response and "team" in response and response["team"] and
                "templates" in response["team"] and "nodes" in response["team"]["templates"]):
            return [template["name"] for template in response["team"]["templates"]["nodes"]]
        return []
    except Exception as e:
        print(f"Failed to retrieve existing templates: {e}")
        return []


def create_test_templates(client, team_id, team_name):
    """Creates test templates in the team."""
    # Get existing templates
    existing_template_names = get_existing_templates(client, team_id)
    print(f"Existing templates: {existing_template_names}")

    # If templates already exist, just exit
    if len(existing_template_names) >= 2:
        print(f"✓ Team {team_name} already has enough templates ({len(existing_template_names)} items)")
        return

    # Create missing templates
    template_data = [
        {
            "name": "Test Bug Report",
            "type": "issue",
            "templateData": {
                "name": "Test Bug Report",
                "description": "# Bug Report\n\n## Description\nA clear and concise description of the bug.\n\n## Steps to Reproduce\n1. Step 1\n2. Step 2\n3. Step 3\n\n## Expected Behavior\nA clear description of what you expected to happen.\n\n## Actual Behavior\nA clear description of what actually happened."
            }
        },
        {
            "name": "Test Feature Project",
            "type": "project",
            "templateData": {
                "name": "Test Feature Project",
                "description": "# Feature Project\n\n## Goal\nA clear and concise description of the project goal.\n\n## Scope\n* Feature 1\n* Feature 2\n* Feature 3\n\n## Timeline\n* Week 1: Planning\n* Week 2-3: Development\n* Week 4: Testing and Release"
            }
        }
    ]

    for template in template_data:
        # Skip if a template with this name already exists
        if template["name"] in existing_template_names:
            print(f"✓ Template {template['name']} already exists, skipping")
            continue

        # API for creating a template
        mutation = """
       mutation CreateTemplate($input: TemplateCreateInput!) {
         templateCreate(input: $input) {
           success
           template {
             id
             name
             type
           }
         }
       }
       """

        variables = {
            "input": {
                "teamId": team_id,
                "name": template["name"],
                "type": template["type"],
                "templateData": template["templateData"]
            }
        }

        try:
            response = client.execute_graphql(mutation, variables)
            if response and "templateCreate" in response and response["templateCreate"]["success"]:
                print(f"✓ Created template: {template['name']} (type: {template['type']})")
            else:
                print(f"✗ Failed to create template: {template['name']}")
        except Exception as e:
            print(f"✗ Error creating template {template['name']}: {e}")


def run_tests():
    """Runs tests after data initialization."""
    import subprocess

    print("\n=== Running tests ===")

    try:
        # Run tests and output the result
        result = subprocess.run(["pytest", "-v", "tests/test_team_manager.py"],
                                capture_output=True, text=True)

        print(result.stdout)

        if result.returncode == 0:
            print("✅ All tests passed successfully!")
        else:
            print(f"❌ Some tests failed (return code: {result.returncode})")

        return result.returncode

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    initialize_test_data()
    # Uncomment to automatically run tests after initialization
    run_tests()