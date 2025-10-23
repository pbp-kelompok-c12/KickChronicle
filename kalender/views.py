from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Kalender
from .forms import ScheduleForm, CsvUploadForm
from datetime import datetime
from icalendar import Calendar, Event
from datetime import timedelta
import pytz
import csv
import io

@login_required
def show_calendar_page(request):
    date_str = request.GET.get("date")
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.today().date()
    else:
        selected_date = datetime.today().date()

    jadwal_list = Kalender.objects.filter(date=selected_date).order_by('time')
    return render(request, "calendar_schedule.html", {
        "matches": jadwal_list,
        "selected_date": selected_date
    })

@login_required
def get_matches_api(request):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse({"matches": []})
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        jadwal_list = Kalender.objects.filter(date=query_date).order_by('time')
        
        match_list = [
            {
                "id": jadwal.id,
                "team_1": jadwal.team_1,
                "team_1_logo": jadwal.team_1_logo,
                "team_2": jadwal.team_2,
                "team_2_logo": jadwal.team_2_logo,
                "start_time": jadwal.time.strftime("%H:%M"),
                "description": jadwal.description or ""
            }
            for jadwal in jadwal_list
        ]

        return JsonResponse({"matches": match_list})
    except (ValueError, TypeError):
        return JsonResponse({"matches": []})

@login_required
def export_kalender_ics(request, kalender_id):
    jadwal = get_object_or_404(Kalender, pk=kalender_id)
    cal = Calendar()
    cal.add('prodid', '-//KickChronicle Calendar//EN')
    cal.add('version', '2.0')
    event = Event()
    event.add('summary', f"{jadwal.team_1} vs {jadwal.team_2}")
    event.add('description', jadwal.description or "Match Schedule")
    
    local_tz = pytz.timezone("Asia/Jakarta")
    start_datetime = local_tz.localize(datetime.combine(jadwal.date, jadwal.time))
    end_datetime = start_datetime + timedelta(hours=2)

    event.add("dtstart", start_datetime)
    event.add("dtend", end_datetime)
    event.add('dtstamp', datetime.now(local_tz))
    event.add('uid', f"{jadwal.id}@kickchronicle.com")
    
    cal.add_component(event)
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename={jadwal.team_1}_vs_{jadwal.team_2}.ics'
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

@login_required
def schedule_detail_view(request, pk):
    jadwal = get_object_or_404(Kalender, pk=pk)
    return render(request, "schedule_detail.html", {"jadwal": jadwal})

@staff_member_required
def import_schedule_csv(request):
    if request.method != 'POST':
        form = CsvUploadForm()
        return render(request, 'import_schedule_csv.html', {'form': form})
    form = CsvUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Form tidak valid. Pastikan file CSV telah dipilih.')
        return render(request, 'import_schedule_csv.html', {'form': form})
    csv_file = request.FILES['csv_file']
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'File harus berformat CSV.')
        return render(request, 'import_schedule_csv.html', {'form': CsvUploadForm()})
    items_created = 0
    items_updated = 0
    try:
        file_data = csv_file.read().decode('utf-8')
        io_string = io.StringIO(file_data)
        reader = csv.reader(io_string)
        next(reader) 
        for row in reader:
            if len(row) < 7: 
                continue

            team_1 = row[0].strip()
            team_2 = row[1].strip()
            date_str = row[2].strip()
            time_str = row[3].strip()
            description = row[4].strip()
            logo_1 = row[5].strip()
            logo_2 = row[6].strip()
            try:
                final_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                final_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                continue

            obj, created = Kalender.objects.update_or_create(
                team_1=team_1,
                team_2=team_2,
                date=final_date,
                defaults={
                    "time": final_time,
                    "description": description,
                    "team_1_logo": logo_1, 
                    "team_2_logo": logo_2, 
                }
            )
            if created:
                items_created += 1
            else:
                items_updated += 1
        messages.success(request, f'{items_created} jadwal baru berhasil diimpor, {items_updated} jadwal berhasil diperbarui.')
        return redirect('kalender:schedule_index')
    except Exception as e:
        messages.error(request, f'Terjadi error saat memproses CSV: {e}')
        return redirect('kalender:import_schedule_csv')

@staff_member_required
def export_schedule_csv(request):
    matches = Kalender.objects.all().order_by('date', 'time')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="schedule_export_manual.csv"'
    writer = csv.writer(response)
    writer.writerow(['team_1', 'team_2', 'date', 'time', 'description', 'team_1_logo', 'team_2_logo'])
    
    for match in matches:
        writer.writerow([
            match.team_1,
            match.team_2,
            match.date.strftime('%Y-%m-%d'),
            match.time.strftime('%H:%M'),
            match.description,
            match.team_1_logo,
            match.team_2_logo  
        ])
    return response