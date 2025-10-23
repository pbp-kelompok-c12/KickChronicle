import csv
import io
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from highlight.models import Highlight
from highlight.forms import HighlightForm, HiglightFormCsv
from django.contrib import messages
from django.db import transaction

def show_main_page(request):
    query = request.GET.get('q')

    if query:
        highlight_list = Highlight.objects.filter(name__icontains=query)
    else:
        highlight_list = Highlight.objects.all()
    
    context = {
        'highlight_list': highlight_list,
        
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

def delete_highlight(request, id):
    if (request.user.is_authenticated and request.user.is_staff):
        highlight = get_object_or_404(Highlight, pk=id)
        highlight.delete()
        return HttpResponseRedirect(reverse('highlight:show_main_page'))
    else:
        return HttpResponseForbidden("403 FORBIDDEN")
    

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
                                manual_thumbnail_url=thumbnail_url_val
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

                return redirect('highlight:add_highlight_csv')
        else: # GET request
            form = HiglightFormCsv()
        return render(request, 'add_highlight_csv.html', {'form': form})
    else:
        return HttpResponseForbidden("403 FORBIDDEN")