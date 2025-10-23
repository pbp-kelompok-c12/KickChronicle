from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

# Assuming Highlight model is defined in app 'highlight' with a UUID primary key 'id'
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    highlight = models.ForeignKey('highlight.Highlight', on_delete=models.CASCADE)
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # Validates rating is between 1 and 5:contentReference[oaicite:4]{index=4}

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "highlight"], name="unique_user_highlight")
        ]  # Enforce one rating per user per highlight:contentReference[oaicite:5]{index=5}

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    highlight = models.ForeignKey('highlight.Highlight', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()  # ← PASTIKAN INI ADA
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    highlight = models.ForeignKey('highlight.Highlight', on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "highlight"], name="unique_user_favorite")
        ]  # Each user can favorite a highlight at most once:contentReference[oaicite:7]{index=7}
