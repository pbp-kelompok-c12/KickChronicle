from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from django.core.files.base import ContentFile
import requests

@receiver(user_signed_up)
def set_google_avatar(request, user, **kwargs):
    social = user.socialaccount_set.filter(provider='google').first()
    if not social:
        return
    pic = (social.extra_data or {}).get('picture')
    if not pic:
        return

    prof = getattr(user, 'profile', None)
    if not prof or prof.image:
        return

    try:
        resp = requests.get(pic, timeout=10)
        resp.raise_for_status()
        prof.image.save(f'google_{user.pk}.jpg', ContentFile(resp.content), save=True)
    except Exception:
        pass


@receiver(social_account_added)
def set_google_avatar_on_first_login(request, sociallogin, **kwargs):
    if sociallogin.account.provider != "google":
        return

    pic = (sociallogin.account.extra_data or {}).get("picture")
    if not pic:
        return

    if "s96" in pic:
        pic = pic.replace("s96", "s256")

    try:
        resp = requests.get(pic, timeout=10)
        resp.raise_for_status()
        profile = sociallogin.user.profile
        if not profile.image:
            profile.image.save(
                f'google_{sociallogin.user.id}.jpg',
                ContentFile(resp.content),
                save=True
            )
    except Exception:
        pass
