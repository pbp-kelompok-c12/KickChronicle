import uuid
from django.db import models
from embed_video.fields import EmbedVideoField

class Highlight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = EmbedVideoField()
    description = models.TextField()
    is_featured = models.BooleanField()
    # possible many to many tim yang main 

    def __str__(self):
        return self.name