from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

class Standing(models.Model):
    SEASON_CHOICES = [
        ('22/23', '2022/2023'),
        ('23/24', '2023/2024'),
        ('24/25', '2024/2025'),
    ]
    
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    position = models.IntegerField()
    team = models.CharField(max_length=100)
    played = models.IntegerField()
    won = models.IntegerField()
    drawn = models.IntegerField()
    lost = models.IntegerField()
    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    goal_difference = models.IntegerField()
    points = models.IntegerField()
    logo_url = models.URLField(max_length=2000, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='standings')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['season', 'position']
        unique_together = ['season', 'position']
        constraints = [
            models.CheckConstraint(
                condition=Q(position__gte=1) & Q(position__lte=20),
                name='tim_standing_position_1_20',
            ),
        ]

    def clean(self):
        super().clean()

        if self.position is None or not (1 <= int(self.position) <= 20):
            raise ValidationError({'position': 'Position must be between 1 and 20.'})

        if Standing.objects.filter(season=self.season, position=self.position).exclude(
            pk=self.pk
        ).exists():
            raise ValidationError(
                {'position': 'This position is already used for the selected season.'}
            )
    
    def __str__(self):
        return f"{self.season} - {self.position}. {self.team}"
