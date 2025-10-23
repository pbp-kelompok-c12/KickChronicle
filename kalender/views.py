from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Kalender
from .forms import ScheduleForm
from datetime import date as dt_date, datetime
import icalendar

def show_calendar_page(request):
    today = dt_date.today()
    jadwal_list = Kalender.objects.filter(date=today)
    return render(request, "calendar_schedule.html", {"matches": jadwal_list})

def get_matches_api(request):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse({"matches": []})
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        jadwal_list = Kalender.objects.filter(date=query_date)
        
        match_list = [
            {
                "id": jadwal.id,
                "team_1": jadwal.team_1,
                "team_1_logo": jadwal.team_1_logo,
                "team_2": jadwal.team_2,
                "team_2_logo": jadwal.team_2_logo,
                "start_time": jadwal.time.strftime("%H:%M")
            }
            for jadwal in jadwal_list
        ]
        return JsonResponse({"matches": match_list})
    except (ValueError, TypeError):
        return JsonResponse({"matches": []})

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

@staff_member_required
def add_schedule_view(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Schedule successfully added!'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    form = ScheduleForm()
    return render(request, 'add_schedule.html', {'form': form})


@staff_member_required
def edit_schedule_view(request, pk):
    jadwal = get_object_or_404(Kalender, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=jadwal)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Changes saved successfully!'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    form = ScheduleForm(instance=jadwal)
    return render(request, 'edit_schedule.html', {'form': form, 'jadwal': jadwal})

@staff_member_required
def delete_schedule_view(request, pk):
    jadwal = get_object_or_404(Kalender, pk=pk)
    if request.method == 'DELETE':
        jadwal.delete()
        return JsonResponse({"success": True, "message": "Schedule berhasil dihapus!"})
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)