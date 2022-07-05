import requests
from django.core.files.base import ContentFile


def get_profile_image(backend, user, response, is_new=False, *args, **kwargs):
    """Pipeline function for User.profile_picture update"""
    if user is None:
        return

    if backend.name == "facebook":
        avatar_url = f"https://graph.facebook.com/{response['id']}/picture?type=large"
    elif backend.name == "google-oauth2":
        avatar_url = response.get("picture")
    else:
        avatar_url = None

    if avatar_url and is_new:
        try:
            avatar_resp = requests.get(avatar_url, params={"type": "large"})
            avatar_resp.raise_for_status()
        except requests.HTTPError as e:
            print(e)  # error log
        else:
            avatar_file = ContentFile(avatar_resp.content)
            user.profile_picture.save(f"{user.id}.jpg", avatar_file)
            user.save(update_fields=["profile_picture"])
