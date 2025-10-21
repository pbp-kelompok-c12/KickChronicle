from django.db import models

# Create your models here.
class Kalender(models.Model):
    team_1 = models.CharField(max_length=100)
    team_2 = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.team_1} vs {self.team_2}"