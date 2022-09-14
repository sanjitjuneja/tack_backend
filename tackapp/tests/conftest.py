import pytest
from django.contrib.auth import authenticate, login
from rest_framework.test import APIClient

from user.models import User


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def user_client_tacker(db, django_db_setup, user_tacker):
    client = APIClient()
    client.force_authenticate(user=user_tacker)
    return client


@pytest.fixture
def user_client_runner(db, django_db_setup, user_runner):
    client = APIClient()
    client.force_authenticate(user=user_runner)
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
        "password": "Testuser123",
    }

    user = User.objects.create_user(**user_data)

    # user = authenticate(None, username=user.username, password="Testuser123")
    # login(None, user)
    return user_data


@pytest.fixture
def user_tacker():
    user_data_tacker = {
        "username": "tacker",
        "email": "testuser@example.com",
        "first_name": "Tacker",
        "last_name": "Tackerov",
        "phone_number": "+375291111111",
        "birthday": "2000-1-1",
        "password": "Tackapp123",
    }
    user_tacker = User.objects.create_user(**user_data_tacker)
    return user_tacker


@pytest.fixture
def user_runner():
    user_data_runner = {
        "username": "runner",
        "email": "testuser@example.net",
        "first_name": "Runner",
        "last_name": "Runnerov",
        "phone_number": "+375299999999",
        "birthday": "2000-1-1",
        "password": "Tackapp123",
    }
    user_runner = User.objects.create_user(**user_data_runner)
    return user_runner


@pytest.fixture
def group_creds():
    return {"name": "Test Group name", "description": "Test Description", "is_public": True}


@pytest.fixture
def tack_creds_with_co():
    return {
        "title": "Test Title",
        "price": "123.55",
        "description": "Test Description",
        "expiration_time": "2022-07-13T11:04:59.062Z",
        "allow_counter_offer": True
    }


@pytest.fixture
def tack_creds_without_co():
    return {
        "title": "Test Tack without CO",
        "price": "1235",
        "description": "Tack without Counter-offer",
        "expiration_time": "2022-07-29T11:04:59.062Z",
        "allow_counter_offer": False
    }

@pytest.fixture
def phone_number():
    return "+375291843236"


@pytest.fixture
def new_user():
    user_data = {
        # "username": "testuser",
        # "email": "test@test.com",
        "first_name": "Test_First_Name",
        "last_name": "Test_Last_Name",
        "phone_number": "+375291843236",
        # "birthday": "2000-1-1",
        "password": "Testuser123",
    }
    return user_data
