import uuid
from django.db import models
from embed_video.backends import detect_backend,UnknownBackendException

class Highlight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=2000)
    manual_thumbnail_url = models.URLField(
        max_length=2000,
        blank=True,
        null=True, # Allow it to be empty
        help_text="Enter URL for a thumbnail if the video URL isn't from YouTube/Vimeo."
    )
    description = models.TextField()
    # mungkin ada field tim
    
    def __str__(self):
        return self.name
    
    @property
    def is_embeddable(self):
        """
        Checks if the URL is from a service recognized
        by django-embed-video.
        """
        try:
            detect_backend(self.url)
            return True
        except UnknownBackendException:
            # If this exception is raised, no backend was found.
            return False