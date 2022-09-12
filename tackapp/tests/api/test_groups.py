import tempfile

from PIL import Image
from django.http import HttpRequest
from django.urls import reverse

from tack_group.models import GroupMembers
from user.models import User


def test_group_creation(user_client_tacker, group_creds):
    image = Image.new('RGB', (100, 100))

    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file)
    tmp_file.seek(0)

    response = user_client_tacker.post(reverse("group-list"), group_creds | {"image": tmp_file}, format="multipart")
    assert response.status_code == 201


def group_invitation(user_client_tacker, user_client_runner, group_creds):
    assert User.objects.count() == 2
    runner = User.objects.get(phone_number="+375299999999")
    tacker = User.objects.get(phone_number="+375291111111")

    response = user_client_tacker.post(reverse("group-list"), group_creds, format="multipart")
    assert response.status_code == 201
    group_id = response.data["id"]

    response = user_client_tacker.post(reverse("groupinvitations-list"), {"group": group_id, "invitee": runner.id})
    assert response.status_code == 201

    response = user_client_runner.get(reverse("groupinvitations-list"))
    assert response.data
    invite_id = response.data[0]["id"]

    return runner, tacker, group_id, invite_id


def test_group_invitation_accept(user_client_tacker, user_client_runner, group_creds):
    runner, tacker, group_id, invite_id = group_invitation(user_client_tacker, user_client_runner, group_creds)

    response = user_client_runner.post(reverse("groupinvitations-accept", args=[invite_id]))
    assert response.data.get("accepted group")
    assert GroupMembers.objects.filter(group=group_id).count() == 2


def test_group_invitation_decline(user_client_tacker, user_client_runner, group_creds):
    runner, tacker, group_id, invite_id = group_invitation(user_client_tacker, user_client_runner, group_creds)

    response = user_client_runner.delete(reverse("groupinvitations-detail", args=[invite_id]))
    assert response.status_code == 204
    assert GroupMembers.objects.filter(group=group_id).count() == 1
