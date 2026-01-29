"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    })
    yield


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=john@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up john@mergington.edu for Chess Club" in data["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "john@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=john@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    # Try to sign up a student who is already registered
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistration from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Club/unregister?email=john@mergington.edu"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_non_registered_participant(client):
    """Test that cannot unregister a student who is not registered"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=john@mergington.edu"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not registered for this activity"


def test_signup_and_unregister_flow(client):
    """Test complete flow of signing up and then unregistering"""
    email = "test@mergington.edu"
    activity = "Programming Class"
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Verify signup
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email in activities_data[activity]["participants"]
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    
    # Verify unregistration
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email not in activities_data[activity]["participants"]


def test_participant_count(client):
    """Test that participant count is tracked correctly"""
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    
    initial_count = len(activities_data["Chess Club"]["participants"])
    
    # Add a participant
    client.post("/activities/Chess Club/signup?email=new@mergington.edu")
    
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    new_count = len(activities_data["Chess Club"]["participants"])
    
    assert new_count == initial_count + 1
