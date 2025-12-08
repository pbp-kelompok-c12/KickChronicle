import csv
import io
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from highlight.models import Highlight
from highlight.forms import HighlightForm, HiglightFormCsv
from django.contrib import messages
from django.db import transaction
from komen_like_rate.models import Favorite
from django.core.paginator import Paginator
from django.utils import timezone

def show_main_page(request):
    query = request.GET.get('q')

    if query:
        highlight_list = Highlight.objects.filter(name__icontains=query).order_by('-id')
    else:
        highlight_list = Highlight.objects.all().order_by('-id')
    
    paginator = Paginator(highlight_list, 12)  # <-- Show 12 highlights per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        # 'highlight_list': highlight_list, # <-- Don't send the full list
        'page_obj': page_obj,              # <-- Send the paginated page object
    }
    return render(request, "highlight_main.html", context)

def show_highlight(request, id):
    highlight = get_object_or_404(Highlight, pk=id)

    # Ambil param "from" dari URL, misalnya ?from=favorite
    from_page = request.GET.get('from')

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(
            user=request.user,
            highlight=highlight
        ).exists()

    context = {
        'highlight': highlight,
        'is_favorited': is_favorited,
        'from_page': from_page,  # supaya bisa ditampilkan di template
    }
    return render(request, "highlight_detail.html", context)

def add_highlight(request):
    if (request.user.is_authenticated and request.user.is_staff):
        form = HighlightForm(request.POST or None)

        if form.is_valid() and request.method == 'POST':
            highlight_entry = form.save(commit = False)
            # product_entry.user = request.user
            highlight_entry.save()
            return redirect('highlight:show_main_page')

        context = {'form': form}
        return render(request, "add_highlight.html", context)
    else:
        return HttpResponseForbidden("403 FORBIDDEN")
    
@csrf_exempt
@user_passes_test(lambda u: u.is_superuser)
def add_highlight_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            new_highlight = Highlight.objects.create(
                name=data['name'],
                url=data['url'],
                manual_thumbnail_url=data.get('manual_thumbnail_url'),
                description=data['description'],
                season=data['season'],
                # created_at is usually auto_now_add=True in models, so no need to set it manually
            )
            
            new_highlight.save()

            return JsonResponse({"status": "success", "message": "Highlight created!"}, status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)
    
def edit_highlight(request, id):
    if (request.user.is_authenticated and request.user.is_staff):
        highlight = get_object_or_404(Highlight, pk=id)
        form = HighlightForm(request.POST or None, instance=highlight)
        if form.is_valid() and request.method == 'POST':
            form.save()
            return redirect('highlight:show_main_page')
        
        context = {
            'form': form
        }

        return render(request, "edit_highlight.html", context)
    else:
        return HttpResponseForbidden("403 FORBIDDEN")

@csrf_exempt
@user_passes_test(lambda u: u.is_superuser)
def edit_highlight_flutter(request, id):
    if request.method == 'POST':
        try:
            highlight = get_object_or_404(Highlight, pk=id)
            data = json.loads(request.body)

            highlight.name = data.get('name', highlight.name)
            highlight.url = data.get('url', highlight.url)
            highlight.manual_thumbnail_url = data.get('manual_thumbnail_url', highlight.manual_thumbnail_url)
            highlight.description = data.get('description', highlight.description)
            highlight.season = data.get('season', highlight.season)
            
            highlight.save()

            return JsonResponse({"status": "success", "message": "Highlight updated!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

def delete_highlight(request, id):
    if (request.user.is_authenticated and request.user.is_staff):
        highlight = get_object_or_404(Highlight, pk=id)
        highlight.delete()
        return HttpResponseRedirect(reverse('highlight:show_main_page'))
    else:
        return HttpResponseForbidden("403 FORBIDDEN")

@csrf_exempt
@user_passes_test(lambda u: u.is_superuser)
def delete_highlight_flutter(request, id):
    if request.method == 'POST':
        try:
            highlight = get_object_or_404(Highlight, pk=id)
            highlight.delete()
            return JsonResponse({"status": "success", "message": "Highlight deleted!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)
    

def add_highlights_csv(request):
    if (request.user.is_authenticated and request.user.is_staff):
        if request.method == 'POST':
            form = HiglightFormCsv(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']

                # Check file extension
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Invalid file format. Please upload a .csv file.')
                    return redirect('highlight:add_highlight_csv') # Adjust URL name

                # try:
                # Decode file and prepare for CSV reader
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                header = next(reader) # Skip header row

                highlights_to_create = []
                skipped_rows = []

                with transaction.atomic():
                    for row_idx, row in enumerate(reader, start=2):
                        # try:
                        # --- Map CSV Columns to Highlight Model Fields ---
                        # Check if essential columns exist
                        if len(row) < 2:
                            skipped_rows.append(f"Row {row_idx}: Too few columns (Need at least Name and URL).")
                            continue

                        name_val = row[0].strip()
                        url_val = row[1].strip()

                        # Optional fields (check if columns exist before accessing)
                        description_val = row[2].strip() if len(row) > 2 and row[2] else "" # Default to empty string
                        thumbnail_url_val = row[3].strip() if len(row) > 3 and row[3] else None # Default to None
                        
                        season_val = row[4].strip()
                        season_mapping = {
                            '2022/2023': '22/23',
                            '2023/2024': '23/24',
                            '2024/2025': '24/25',
                        }

                        if season_val in season_mapping:
                            season_val = season_mapping[season_val]
                        elif season_val not in season_mapping.values():
                            season_val = None

                        # Basic Validation
                        # if not name_val:
                        #     skipped_rows.append(f"Row {row_idx}: Name is missing.")
                        #     continue
                        # if not url_val:
                        #     skipped_rows.append(f"Row {row_idx}: URL is missing.")
                        #     continue

                        # Add Highlight instance to list for bulk creation
                        highlights_to_create.append(
                            Highlight(
                                name=name_val,
                                url=url_val,
                                description=description_val,
                                manual_thumbnail_url=thumbnail_url_val,
                                season=season_val
                                # created_at is handled automatically by the model's default
                            )
                        )
                    # except IndexError:
                    #     skipped_rows.append(f"Row {row_idx}: Error reading columns (IndexError).")
                    #     continue
                    # except Exception as e: # Catch other potential errors per row
                    #     skipped_rows.append(f"Row {row_idx}: Unexpected error ({e}).")
                    #     continue

                # Bulk create highlights
                # if highlights_to_create:
                created_objects = Highlight.objects.bulk_create(highlights_to_create)
                messages.success(request, f"Successfully imported {len(created_objects)} highlights.")
                # else:
                #     messages.info(request, "No new highlights found to import.")

                # Report skipped rows
                # if skipped_rows:
                #     messages.warning(request, "Some rows were skipped:")
                #     for skipped in skipped_rows[:10]:
                #         messages.warning(request, skipped)
                #     if len(skipped_rows) > 10:
                #         messages.warning(request, f"...and {len(skipped_rows) - 10} more.")

                # except UnicodeDecodeError:
                #     messages.error(request, 'Error reading file. Please ensure it is UTF-8 encoded.')
                # except csv.Error as e:
                #     messages.error(request, f'Error processing CSV file structure: {e}')
                # except Exception as e:
                #     messages.error(request, f'An unexpected error occurred during import: {e}')

                return redirect('highlight:show_main_page')
        else: # GET request
            form = HiglightFormCsv()
        return render(request, 'add_highlight_csv.html', {'form': form})
    else:
        return HttpResponseForbidden("403 FORBIDDEN")

@csrf_exempt
@user_passes_test(lambda u: u.is_superuser)
def add_highlights_csv_flutter(request):
    if request.method == 'POST':
        try:
            # 1. Check if file is present
            if 'csv_file' not in request.FILES:
                return JsonResponse({"status": "error", "message": "No file uploaded"}, status=400)

            csv_file = request.FILES['csv_file']

            # 2. Check extension
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({"status": "error", "message": "File is not a CSV"}, status=400)

            # 3. Read and Decode
            file_data = csv_file.read().decode('utf-8')
            io_string = io.StringIO(file_data)
            reader = csv.reader(io_string)
            
            # Skip header (assuming 1st row is header based on your screenshot logic)
            next(reader, None) 

            highlights_to_create = []
            skipped_rows = []

            # 4. Parse Rows
            # row[0] -> Name
            # row[1] -> URL
            # row[2] -> Description (optional)
            # row[3] -> Manual Thumbnail URL (optional)
            # row[4] -> Season (e.g., '2024/2025')

            season_mapping = {
                '2022/2023': '22/23',
                '2023/2024': '23/24',
                '2024/2025': '24/25',
            }

            for row_idx, row in enumerate(reader, start=2):
                if len(row) < 2: # Need at least Name and URL
                    skipped_rows.append(f"Row {row_idx}: Too few columns")
                    continue

                name = row[0].strip()
                url = row[1].strip()
                
                if not name or not url:
                    skipped_rows.append(f"Row {row_idx}: Missing name or URL")
                    continue

                description = row[2].strip() if len(row) > 2 else ""
                manual_thumbnail_url = row[3].strip() if len(row) > 3 else None
                if manual_thumbnail_url == "":
                    manual_thumbnail_url = None
                
                season_raw = row[4].strip() if len(row) > 4 else ""
                season_val = season_mapping.get(season_raw) 
                
                # If season not found, fallback or skip? 
                # For simplicity, let's default to None or handle it.
                # Your screenshot shows strict checking, but let's be lenient for the flutter test.
                if not season_val:
                     skipped_rows.append(f"Row {row_idx}: Invalid season format '{season_raw}'")
                     continue

                highlights_to_create.append(Highlight(
                    name=name,
                    url=url,
                    description=description,
                    manual_thumbnail_url=manual_thumbnail_url,
                    season=season_val
                ))

            # 5. Bulk Create
            if highlights_to_create:
                Highlight.objects.bulk_create(highlights_to_create)
                return JsonResponse({
                    "status": "success", 
                    "message": f"Successfully imported {len(highlights_to_create)} highlights.",
                    "skipped": skipped_rows
                }, status=201)
            else:
                return JsonResponse({
                    "status": "error", 
                    "message": "No valid rows found to import.",
                    "skipped": skipped_rows
                }, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

def highlight_json(request):
    highlight_list = Highlight.objects.all()

    query = request.GET.get('q')
    if query:
        highlight_list = highlight_list.filter(name__icontains=query)

    paginator = Paginator(highlight_list,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    data = []

    for highlight in page_obj:
        home_standing = None
        if highlight.home: # checks if self.home returns a Standing object
            home_standing = {
                "team": highlight.home.team,    # Adjust field names to match your Standing model
                "played": highlight.home.played,
                "won": highlight.home.won,
                "drawn": highlight.home.drawn,
                "lost": highlight.home.lost,
            }

        # 2. Access the @property 'away'
        away_standing = None
        if highlight.away:
            away_standing = {
                "team": highlight.away.team,
                "played": highlight.away.played,
                "won": highlight.away.won,
                "drawn": highlight.away.drawn,
                "lost": highlight.away.lost,
            }
        
        data.append({
            "id": highlight.pk,
            "name": highlight.name,
            "url": highlight.url,
            "description": highlight.description,
            "season": highlight.season,
            "manual_thumbnail_url": highlight.manual_thumbnail_url,
            "created_at": highlight.created_at.isoformat(),
            "home_standing": home_standing, 
            "away_standing": away_standing,
        })


    return JsonResponse(data, safe=False)

@csrf_exempt
@user_passes_test(lambda u: u.is_superuser)
def admin_highlight_flutter(request):
    if request.method == 'GET':
        # Return all highlights for the admin list
        highlights = Highlight.objects.all().order_by('-created_at')
        data = []
        for item in highlights:
            data.append({
                "id": item.pk,
                "name": item.name,
                "url": item.url,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"), # Simple string format
            })
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        # Bulk Delete
        try:
            data = json.loads(request.body)
            ids_to_delete = data.get('ids', [])
            
            if not ids_to_delete:
                return JsonResponse({"status": "error", "message": "No IDs provided"}, status=400)

            # Filter and delete
            # Assuming IDs are UUIDs or ints, Django handles the list lookup
            deleted_count, _ = Highlight.objects.filter(pk__in=ids_to_delete).delete()
            
            return JsonResponse({
                "status": "success", 
                "message": f"Successfully deleted {deleted_count} highlights."
            }, status=200)
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)