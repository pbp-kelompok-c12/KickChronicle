import re
import uuid
from django.db import models
from django.utils import timezone
from embed_video.backends import detect_backend,UnknownBackendException
from tim.models import Standing

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
    created_at = models.DateTimeField(default=timezone.now)
    season = models.CharField(
        max_length=10,
        choices=Standing.SEASON_CHOICES, # Borrows choices from Standing
        null=True,
        blank=True,
        help_text="Select the season this highlight belongs to."
    )

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
    
    @property
    def _match_teams(self):
        """
        Internal helper to parse team names from the 'name' field.
        Caches the result on the object instance to avoid re-parsing.
        Returns a tuple (home_name, away_name) or (None, None).
        """
        if hasattr(self, '_cached_team_names'):
            return self._cached_team_names

        match = re.match(r'^(.*?)(\s+(vs|v|v\.)\s+)(.*)$', self.name, re.IGNORECASE)
        
        if match:
            home_name = match.group(1).strip()
            away_name = match.group(4).strip()
            self._cached_team_names = (home_name, away_name)
            return (home_name, away_name)
        
        self._cached_team_names = (None, None)
        return (None, None)

    @property
    def home(self):
        """
        Returns the Standing object for the Home team,
        based on the 'name' field and linked 'season' string.
        """
        home_name, _ = self._match_teams
        
        # Exit if name couldn't be parsed or season string isn't set
        if not home_name or not self.season:
            return None
            
        current_season_str = self.season
        
        try:
            home_team_standing = Standing.objects.get(
                season=current_season_str,
                team__iexact=home_name
            )
            return home_team_standing
        except Standing.DoesNotExist:
            return None
        except Standing.MultipleObjectsReturned:
             return Standing.objects.filter(
                season=current_season_str,
                team__iexact=home_name
            ).first()

    @property
    def away(self):
        """
        Returns the Standing object for the Away team,
        based on the 'name' field and linked 'season' string.
        """
        _, away_name = self._match_teams
        
        # Exit if name couldn't be parsed or season string isn't set
        if not away_name or not self.season:
            return None
            
        current_season_str = self.season
        
        try:
            away_team_standing = Standing.objects.get(
                season=current_season_str,
                team__iexact=away_name
            )
            return away_team_standing
        except Standing.DoesNotExist:
            return None
        except Standing.MultipleObjectsReturned:
             return Standing.objects.filter(
                season=current_season_str,
                team__iexact=away_name
            ).first()