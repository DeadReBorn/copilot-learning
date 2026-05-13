import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture to provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture to reset activities to a known state before each test.
    This ensures test isolation by resetting participant lists.
    """
    from src.app import activities
    
    # Store original state
    original_state = {
        activity: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for activity, details in activities.items()
    }
    
    yield activities
    
    # Restore original state after test
    for activity, details in original_state.items():
        activities[activity]["participants"] = details["participants"].copy()
