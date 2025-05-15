import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from linear_api.client import LinearClient
from linear_api.domain import (
   LinearIssue,
   LinearUser,
   LinearState,
   LinearLabel,
   LinearProject,
   LinearTeam,
   LinearAttachment,
)


def main():
   # Get API key from environment variables
   api_key = os.environ.get("LINEAR_API_KEY")
   if not api_key:
       print("Error: LINEAR_API_KEY environment variable is not set")
       return

   # Create Linear API client
   client = LinearClient(api_key=api_key)

   # List of all models to check
   models = [
       LinearIssue,
       LinearUser,
       LinearState,
       LinearLabel,
       LinearProject,
       LinearTeam,
       LinearAttachment,
   ]

   # Check each model
   for model_class in models:
       print(f"\n{'=' * 80}")
       print(f"Checking model: {model_class.__name__}")
       print(f"{'=' * 80}")

       try:
           # Call validate_schema method for current model
           result = client.validate_schema(model_class)

           # Output validation results
           completeness = result.get("completeness", 0) * 100
           print(f"Model completeness: {completeness:.1f}%")

           if result.get("missing_in_model"):
               print("\nFields missing in model:")
               for field in result["missing_in_model"]:
                   print(f"  - {field}")

           if result.get("extra_in_model"):
               print("\nExtra fields in model (not in GraphQL schema):")
               for field in result["extra_in_model"]:
                   print(f"  - {field}")

           # Check for soft deletion fields
           soft_delete_fields = ["archivedAt", "trashed", "canceledAt", "completedAt", "autoArchivedAt"]
           common_fields = set(result.get("common_fields", []))

           print("\nSoft deletion fields check:")
           for field in soft_delete_fields:
               if field in common_fields:
                   print(f"  ✅ {field} - present in model and API")
               elif field in result.get("missing_in_model", []):
                   print(f"  ❌ {field} - missing in model, but exists in API")
               elif field in result.get("extra_in_model", []):
                   print(f"  ⚠️ {field} - present in model, but missing in API")
               else:
                   print(f"  ℹ️ {field} - not applicable to this model")

       except Exception as e:
           print(f"Error checking model {model_class.__name__}: {e}")


if __name__ == "__main__":
   main()