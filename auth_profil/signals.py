# auth_profil/signals.py
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from django.core.files.base import ContentFile
import requests

@receiver(social_account_added)
def set_google_avatar_on_first_login(request, sociallogin, **kwargs):
    if sociallogin.account.provider != "google":
        return

    picture_url = (sociallogin.account.extra_data or {}).get("picture")
    if not picture_url:
        return

    profile = sociallogin.user.profile

    current = (profile.image.name or "")
    if not (current.endswith("default.png") or current == "profile_pics/default.png"):
        return

    try:
        if "s96" in picture_url:
            picture_url = picture_url.replace("s96", "s256")

        resp = requests.get(picture_url, timeout=10)
        resp.raise_for_status()

        profile.image.save(
            f"google_{sociallogin.user.pk}.jpg",
            ContentFile(resp.content),
            save=True
        )
    except Exception as e:
        print("Failed to set google avatar:", e)
        return
