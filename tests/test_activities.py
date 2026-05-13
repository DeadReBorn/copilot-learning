import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / root endpoint"""
    
    def test_root_redirect_to_static_index(self, client, reset_activities):
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities
    
    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_details in activities.items():
            assert set(activity_details.keys()) == expected_keys
            assert isinstance(activity_details["description"], str)
            assert isinstance(activity_details["schedule"], str)
            assert isinstance(activity_details["max_participants"], int)
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_has_initial_participants(self, client, reset_activities):
        # Arrange (nothing needed, activities are pre-populated)
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_details in activities.items():
            # Each activity should have at least 2 initial participants
            assert len(activity_details["participants"]) >= 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert len(updated_participants) == len(initial_participants) + 1
        assert email in updated_participants
    
    def test_signup_activity_not_found(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_multiple_activities(self, client, reset_activities):
        # Arrange
        email = "multiactivity@mergington.edu"
        activity_1 = "Chess Club"
        activity_2 = "Programming Class"
        
        # Act
        response_1 = client.post(
            f"/activities/{activity_1}/signup",
            params={"email": email}
        )
        response_2 = client.post(
            f"/activities/{activity_2}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_1]["participants"]
        assert email in activities[activity_2]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was removed
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert len(updated_participants) == len(initial_participants) - 1
        assert email not in updated_participants
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"  # Not registered
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # Act - First signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Sign up again
        signup_again_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert signup_response.status_code == 200
        assert unregister_response.status_code == 200
        assert signup_again_response.status_code == 200
        
        # Verify student is registered again
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
