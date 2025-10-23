from django.contrib import admin
from .models import Standing

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ['season', 'position', 'team', 'logo_url', 'played', 'won', 'drawn', 'lost', 'points', 'uploaded_by']
    list_filter = ['season', 'uploaded_by']
    search_fields = ['team']
    ordering = ['season', 'position']
