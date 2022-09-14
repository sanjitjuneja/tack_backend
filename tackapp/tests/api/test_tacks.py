import datetime

from django.urls import reverse

from core.choices import TackStatus, OfferType
from tack.models import Tack
from user.models import User


def test_tack_create(user_client_tacker, tack_creds_with_co):
    count_tacks_before = Tack.objects.count()
    tacker = User.objects.get(phone_number="+375291111111")

    response = user_client_tacker.post(reverse("tack-list"), tack_creds_with_co)
    count_tacks_after = Tack.objects.count()
    assert response.status_code == 201
    assert response.data["id"]
    assert response.data["title"] == tack_creds_with_co["title"]
    assert response.data["price"] == tack_creds_with_co["price"]
    assert response.data["description"] == tack_creds_with_co["description"]
    assert response.data["allow_counter_offer"] == tack_creds_with_co["allow_counter_offer"]
    assert response.data["status"] == TackStatus.labels[0]  # 'Preparation'
    assert response.data["tacker"] == tacker.id
    assert count_tacks_after - count_tacks_before == 1


def test_tacks_me(user_client_tacker, user_client_runner, tack_creds_with_co):
    response = user_client_tacker.post(reverse("tack-list"), tack_creds_with_co)
    assert response.status_code == 201

    response = user_client_tacker.get(reverse("tack-me"))
    assert response.status_code == 200
    assert response.data

    response = user_client_runner.get(reverse("tack-me"))
    assert not response.data


def test_offer_create(user_client_tacker, user_client_runner, tack_creds_with_co):
    runner = User.objects.get(phone_number="+375299999999")
    response = user_client_tacker.post(reverse("tack-list"), tack_creds_with_co)
    tack_id = response.data["id"]
    price = "123.44"
    response = user_client_runner.post(reverse("offer-list"), {"tack": tack_id, "price": price})
    assert response.status_code == 201
    assert response.data["id"]
    assert response.data["price"] == price
    assert response.data["tack"] == tack_id
    assert response.data["offer_type"] == OfferType.labels[1]
    assert response.data["runner"] == runner.id
    assert response.data["is_accepted"] is False


def test_offer_tack_without_co(user_client_tacker, user_client_runner, tack_creds_without_co):
    response = user_client_tacker.post(reverse("tack-list"), tack_creds_without_co)
    tack_id = response.data["id"]
    price = "1234"
    assert response.status_code == 201

    response = user_client_runner.post(reverse("offer-list"), {"tack": tack_id, "price": price})
    assert response.status_code == 403


def test_offer_me(user_client_tacker, user_client_runner, tack_creds_with_co):
    response = user_client_tacker.post(reverse("tack-list"), tack_creds_with_co)
    tack_id = response.data["id"]
    price = "123.44"
    response = user_client_runner.post(reverse("offer-list"), {"tack": tack_id, "price": price})
    offer_id = response.data["id"]

    response = user_client_runner.get(reverse("offer-me"))

    print(f"__________________________ {response.data = }")
    assert response.data

    response = user_client_tacker.get(reverse("offer-me"))
    assert not response.data

    response = user_client_tacker.get(reverse("tack-offers", args=[tack_id]))
    assert response.data
    assert response.data[0]["id"] == offer_id

    # Only owner can see Offers of the current Tack
    response = user_client_runner.get(reverse("tack-offers", args=[tack_id]))
    assert response.status_code == 403


def test_offer_positive_case(user_client_tacker, user_client_runner, tack_creds_with_co):
    response = user_client_tacker.post(reverse("tack-list"), tack_creds_with_co)
    tack_id = response.data["id"]
    price = "123.44"
    response = user_client_runner.post(reverse("offer-list"), {"tack": tack_id, "price": price})
    offer_id = response.data["id"]

    response = user_client_tacker.post(reverse("offer-accept", args=[offer_id]))
    print(f"{response.data = }")
    assert response.status_code == 200

    response = user_client_runner.post(
        reverse("tack-complete", args=[tack_id]),
        {"message": "I completed your tack successfully"})
    assert response.status_code == 200

    response = user_client_tacker.post(reverse("tack-confirm-complete", args=[tack_id]))
    tack = Tack.objects.get(pk=tack_id)
    assert response.status_code == 200
    assert tack.status == TackStatus.FINISHED


