import pytest
from django.contrib.auth import authenticate, login
from rest_framework.test import APIClient

from user.models import User


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def user_client(db, django_db_setup):
    user = User.objects.create_user("testuser", "test@test.com", "Testuser123")
    client = APIClient()
    client.force_authenticate(user=user)

    return client


@pytest.fixture
def user_creds():
    user_data = {
        "username": "Test_Username",
        "email": "testuser@example.com",
        "first_name": "Test_First_Name",
        "last_name": "Test_Last_Name",
        "phone_number": "+375291843236",
        "birthday": "2000-1-1",
        "password": "Testuser123"
    }

    user = User.objects.create_user(**user_data)

    # user = authenticate(None, username=user.username, password="Testuser123")
    # login(None, user)
    return user_data


@pytest.fixture
def phone_number():
    return "+375291843236"


@pytest.fixture
def new_user():
    user_data = {
        "username": "testuser",
        "email": "test@test.com",
        "first_name": "Test_First_Name",
        "last_name": "Test_Last_Name",
        "phone_number": "+375291843236",
        "birthday": "2000-1-1",
        "password": "Testuser123"
    }
    return user_data
