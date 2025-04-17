import pytest
from datetime import datetime

from linear_api.get_user import fetch_linear_user, get_user_email_map
from linear_api.domain import LinearUser


class TestGetUser:
    """Tests for the get_user.py module."""

    def test_get_user_email_map(self):
        """Test that get_user_email_map returns a dictionary of user IDs to emails."""
        # Call the function
        user_email_map = get_user_email_map()

        # Verify the response is a dictionary
        assert isinstance(user_email_map, dict)

        # If users exist, verify the structure of the map
        if user_email_map:
            # Get the first user ID and email
            user_id, email = next(iter(user_email_map.items()))

            # Verify the types
            assert isinstance(user_id, str)
            assert isinstance(email, str)

            # Verify the email has a valid format (contains @)
            assert '@' in email

    def test_fetch_linear_user(self):
        """
        Test fetching a user by ID.
        
        This test requires a valid user ID and API key.
        If no user ID is available, the test will be skipped.
        """
        # Get all users first to find a valid user ID
        user_email_map = get_user_email_map()
        
        # Skip if no users are available
        if not user_email_map:
            pytest.skip("No users available for testing")
        
        # Get the first user ID
        user_id = next(iter(user_email_map.keys()))
        
        # Use an empty string as API key since it's not actually used in the implementation
        # (The implementation uses the API key from environment variables)
        api_key = ""
        
        # Fetch the user
        user = fetch_linear_user(user_id, api_key)
        
        # Verify the user is a LinearUser instance
        assert isinstance(user, LinearUser)
        
        # Verify the user has the expected properties
        assert user.id == user_id
        assert isinstance(user.createdAt, datetime)
        assert isinstance(user.updatedAt, datetime)
        assert isinstance(user.name, str)
        assert isinstance(user.displayName, str)
        assert isinstance(user.email, str)

        
        # Verify the email matches what we got from the email map
        assert user.email == user_email_map[user_id]

    def test_fetch_linear_user_invalid_id(self):
        """Test fetching a user with an invalid ID."""
        # Use a clearly invalid user ID
        invalid_user_id = "invalid_user_id_that_does_not_exist"
        api_key = ""
        
        # This should raise an exception
        with pytest.raises(Exception):
            fetch_linear_user(invalid_user_id, api_key)


