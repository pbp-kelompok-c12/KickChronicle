from django.db import models
from django.templatetags.static import static

# Create your models here.
class Kalender(models.Model):
    team_1 = models.CharField(max_length=100)
    team_1_logo = models.URLField(blank=True, null=True)
    team_2 = models.CharField(max_length=100)
    team_2_logo = models.URLField(blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField(blank=True, null=True)

    @staticmethod
    def _resolve_logo_path(value: str | None) -> str:
        """
        Convert stored logo values to a URL that the Django web UI can load.

        Data in DB may contain Flutter-style paths (e.g. `assets/images/...`).
        For the browser, we serve static files via `/static/...`.
        """
        if not value:
            return ""

        src = str(value).strip()
        if not src:
            return ""

        lower = src.lower()
        if lower.startswith(("http://", "https://", "data:")):
            return src

        if src.startswith("/static/") or src.startswith("/media/"):
            return src

        if src.startswith("static/") or src.startswith("media/"):
            return f"/{src}"

        # Flutter asset paths -> Django static paths
        if src.startswith("/assets/"):
            src = src[len("/assets/") :]
        elif src.startswith("assets/"):
            src = src[len("assets/") :]

        # Normalize `/images/...` -> `images/...` before `static()`
        if src.startswith("/images/"):
            src = src.lstrip("/")

        if src.startswith("images/"):
            return static(src)

        # If only filename is stored, assume it lives in images/team.
        if "/" not in src:
            return static(f"images/team/{src}")

        return src

    @property
    def team_1_logo_url(self) -> str:
        return self._resolve_logo_path(self.team_1_logo)

    @property
    def team_2_logo_url(self) -> str:
        return self._resolve_logo_path(self.team_2_logo)

    def __str__(self):
        return f"{self.team_1} vs {self.team_2} on {self.date}"
