from django.db import models

# Create your models here.
class Kalender(models.Model):
    team_1 = models.CharField(max_length=100)
    team_1_logo = models.URLField(blank=True, null=True)
    team_2 = models.CharField(max_length=100)
    team_2_logo = models.URLField(blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.team_1} vs {self.team_2} on {self.date}"

