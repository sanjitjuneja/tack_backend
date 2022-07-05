from django.urls import reverse

from socials.models import PhoneVerification


def test_phone_registration(anon_client, phone_number, db, new_user, mocker):
    """Testing full registration process by phone number"""

    # Mocking send SMS function
    mocker.patch('socials.sms_service.TwilioClient.send_signup_message', return_value="SM123123123")

    response = anon_client.post(reverse("signup-send-code"), {"phone_number": phone_number})
    uuid = response.data.get("uuid")
    assert response.status_code == 200
    assert uuid

    # Imitating that we got our SMS-code
    sms_code = PhoneVerification.objects.last().sms_code
    response = anon_client.post(reverse("verify-sms-code"), {"sms_code": sms_code, "uuid": uuid})
    assert response.status_code == 200

    registration_data = {"uuid": uuid, "user": new_user}
    response = anon_client.post(reverse("signup-registration"), registration_data)
    assert response.status_code == 200
    assert new_user.get("username") == response.data.get("user").get("username")


def test_check_profile(user_client, db):
    response = user_client.get(reverse("accounts-profile"))
    assert response.status_code == 200
    assert response.data.get("is_authenticated") == "True"
    assert response.data.get("email") == "test@test.com"


def test_login(anon_client, db, user_creds):
    response = anon_client.post(
        reverse("accounts-login"),
        {
            "username": user_creds["username"],
            "password": user_creds["password"]
        })

    assert response.status_code == 200
