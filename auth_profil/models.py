from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='profile_pics/default.png', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(pre_save, sender=Profile)
def delete_old_image_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Profile.objects.get(pk=instance.pk).image
    except Profile.DoesNotExist:
        return
    new = instance.image
    if old and old.name != (new.name if new else None) and not old.name.endswith('default.png'):
        old.storage.delete(old.name)

@receiver(post_delete, sender=Profile)
def delete_image_on_delete(sender, instance, **kwargs):
    if instance.image and instance.image.name and not instance.image.name.endswith('default.png'):
        instance.image.storage.delete(instance.image.name)