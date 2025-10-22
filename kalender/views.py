# kalender/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Kalender
from datetime import date as dt_date, datetime
import icalendar
from .forms import ScheduleForm

def show_calendar_page(request):
    today = dt_date.today()
    jadwal_list = Kalender.objects.filter(date=today)
    return render(request, "calendar_schedule.html", {"matches": jadwal_list})

def get_matches_api(request):
    date_str = request.GET.get("date")
    jadwal_list = Kalender.objects.filter(date=date_str)
    
    match_list = []
    for jadwal in jadwal_list:
        match_list.append({
            "id": jadwal.id,
            "team_1": jadwal.team_1,
            "team_2": jadwal.team_2,
            "start_time": jadwal.time.strftime("%H:%M")
        })
    return JsonResponse({"matches": match_list})

def export_kalender_ics(request, kalender_id):
    jadwal = get_object_or_404(Kalender, pk=kalender_id)
    cal = icalendar.Calendar()
    event = icalendar.Event() 
    event.add("summary", f"Pertandingan: {jadwal.team_1} vs {jadwal.team_2}")
    start_datetime = datetime.combine(jadwal.date, jadwal.time)
    event.add("dtstart", start_datetime)

    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response["Content-Disposition"] = f"attachment; filename=jadwal-{jadwal.id}.ics"
    return response

def add_schedule_view(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('kalender:schedule_index') 
    else:
        form = ScheduleForm()
    return render(request, 'kalender/add_schedule.html', {'form': form})