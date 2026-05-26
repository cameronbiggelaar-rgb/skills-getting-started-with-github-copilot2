"""Tests for the FastAPI application endpoints."""
import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        # Arrange
        # Activities are already initialized via the reset_activities fixture
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activities include required fields."""
        # Arrange
        expected_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Assert
        assert response.status_code == 200
        for field in expected_fields:
            assert field in chess_club
    
    def test_get_activities_includes_initial_participants(self, client, reset_activities):
        """Test that initial participants are returned."""
        # Arrange
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        chess_participants = response.json()["Chess Club"]["participants"]
        
        # Assert
        assert response.status_code == 200
        for participant in expected_participants:
            assert participant in chess_participants


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds a participant to an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert "Signed up" in data["message"]
    
    def test_signup_participant_appears_in_activity(self, client, reset_activities):
        """Test that signed-up participant appears in activity participants list."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        
        # Assert
        assert response.status_code == 200
        assert new_email in participants
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signup to non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant_returns_400(self, client, reset_activities):
        """Test that signing up twice returns an error."""
        # Arrange
        activity_name = "Chess Club"
        duplicate_email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={duplicate_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"]
    
    def test_signup_to_different_activity_succeeds(self, client, reset_activities):
        """Test that same email can sign up for different activities."""
        # Arrange
        email = "dual@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        response_check = client.get("/activities")
        activities_data = response_check.json()
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities_data[activity1]["participants"]
        assert email in activities_data[activity2]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that DELETE removes a participant from an activity."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert "Unregistered" in data["message"]
    
    def test_unregister_participant_no_longer_in_activity(self, client, reset_activities):
        """Test that unregistered participant is removed from list."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity_name}/participants?email={email}")
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        
        # Assert
        assert response.status_code == 200
        assert email not in participants
    
    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregistering from non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "someone@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{nonexistent_activity}/participants?email={email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in data["detail"]
    
    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """Test that unregistering non-existent participant returns 404."""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "nonexistent@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/participants?email={nonexistent_email}")
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in data["detail"]
    
    def test_cannot_unregister_twice(self, client, reset_activities):
        """Test that unregistering the same participant twice fails."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - First unregister
        response1 = client.delete(f"/activities/{activity_name}/participants?email={email}")
        
        # Act - Second unregister
        response2 = client.delete(f"/activities/{activity_name}/participants?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 404


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_full_signup_and_unregister_flow(self, client, reset_activities):
        """Test complete flow: signup, verify, unregister, verify."""
        # Arrange
        activity_name = "Chess Club"
        email = "integration@mergington.edu"
        
        # Act - Sign up
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act - Verify signup
        response2 = client.get("/activities")
        signup_participants = response2.json()[activity_name]["participants"]
        
        # Act - Unregister
        response3 = client.delete(f"/activities/{activity_name}/participants?email={email}")
        
        # Act - Verify unregister
        response4 = client.get("/activities")
        unregister_participants = response4.json()[activity_name]["participants"]
        
        # Assert
        assert response1.status_code == 200
        assert email in signup_participants
        assert response3.status_code == 200
        assert email not in unregister_participants
    
    def test_availability_updates_after_signup(self, client, reset_activities):
        """Test that availability decreases after signup."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newuser@mergington.edu"
        
        # Act - Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity_name]["participants"])
        
        # Act - Sign up
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Act - Get final count
        response2 = client.get("/activities")
        final_count = len(response2.json()[activity_name]["participants"])
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert final_count == initial_count + 1
