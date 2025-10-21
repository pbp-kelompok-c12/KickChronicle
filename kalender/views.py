from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ics import Calendar, Event
from .models import Kalender

def export_kalender_ics(request, kalender_id):
    kalender = get_object_or_404(Kalender, pk=kalender_id)
    c = Calendar()
    e = Event()

    e.name = f"Pertandingan: {kalender.team_1} vs {kalender.team_2}"
    e.begin = kalender.start
    e.end = kalender.end
    e.location = kalender.location
    e.description = kalender.description
    c.events.add(e)

    response = HttpResponse(str(c), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="kalender-{kalender.team_1}-vs-{kalender.team_2}.ics"'
    return response