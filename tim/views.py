from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.templatetags.static import static
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
import csv
import io
import json
from .models import Standing
from .forms import StandingUploadForm

def get_calendar_team_name(team_name: str) -> str:
    """
    Map team name from standings (Tim module) to the team name used in Kalender.

    Reason: calendar CSV uses names like "Liverpool FC" while standings CSV uses
    "Liverpool". This mapping keeps standings as-is, but ensures team schedule
    lookup finds matches.
    """
    if not team_name:
        return ""

    name = str(team_name).strip()
    if not name:
        return ""

    # Only map known differences between standings CSV and calendar CSV.
    mapping = {
        "Liverpool": "Liverpool FC",
        "Arsenal": "Arsenal FC",
        "Chelsea": "Chelsea FC",
        "Everton": "Everton FC",
        "Fulham": "Fulham FC",
        "Brentford": "Brentford FC",
        "Bournemouth": "AFC Bournemouth",
        "Burnley": "Burnley FC",
        "Sunderland": "Sunderland AFC",
    }

    return mapping.get(name, name)

def get_team_logo_url(team_name):
 
    special_mappings = {
        'Manchester City': 'manchester-city',
        'Manchester United': 'manchester-united',
        'Newcastle United': 'newcastle',
        'Tottenham Hotspur': 'tottenham',
        'Brighton & Hove Albion': 'brighton',
        'West Ham United': 'west-ham',
        'Crystal Palace': 'crystal-palace',
        'Nottingham Forest': 'nottingham-forest',
        'Wolverhampton Wanderers': 'wolves',
        'Leeds United': 'leeds-united',
        'Leicester City': 'leicester',
        'Aston Villa': 'aston-villa',
        'Luton Town': 'luton-town',
        'Sheffield United': 'sheffield-united',
        'Ipswich Town': 'ipswich'
    }
    
    if team_name in special_mappings:
        team_slug = special_mappings[team_name]
    else:
        team_slug = slugify(team_name.lower())
    

    logo_path = f'images/team/england_{team_slug}_256x256.png'
    
    return static(logo_path)

@login_required
def standings_page(request):
    """Main page to display standings tables"""
    form = StandingUploadForm()
    context = {
        'form': form,
    }
    return render(request, 'standings.html', context)

def get_standings_json(request):
    """API endpoint to get standings data filtered by season"""
    season = request.GET.get('season', None)
    
    if season:
        standings = Standing.objects.filter(season=season)
    else:
        standings = Standing.objects.all()
    
    data = []
    for standing in standings:
        # Kirim URL absolut agar Flutter tidak perlu merakit host lagi.
        logo_url = request.build_absolute_uri(get_team_logo_url(standing.team))

        data.append({
            'id': standing.id,
            'season': standing.season,
            'position': standing.position,
            'team': standing.team,
            'calendar_team': get_calendar_team_name(standing.team),
            'played': standing.played,
            'won': standing.won,
            'drawn': standing.drawn,
            'lost': standing.lost,
            'goals_for': standing.goals_for,
            'goals_against': standing.goals_against,
            'goal_difference': standing.goal_difference,
            'points': standing.points,
            'logo_url': logo_url,
        })
    
    return JsonResponse({'standings': data}, safe=False)

@login_required
@require_POST
def upload_standings_ajax(request):
    """AJAX endpoint to upload CSV file and save standings"""
    if not request.user.is_superuser:
        return JsonResponse({
            'status': 'error',
            'message': 'Only superusers can upload standings data'
        }, status=403)
    
    form = StandingUploadForm(request.POST, request.FILES)
    
    if form.is_valid():
        season = form.cleaned_data['season']
        csv_file = request.FILES['csv_file']
        
        # Validate file extension
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({
                'status': 'error',
                'message': 'File must be a CSV file'
            }, status=400)
        
        try:
            Standing.objects.filter(season=season).delete()
            
            # Read and parse CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            standings_to_create = []
            for row in reader:
                standing = Standing(
                    season=season,
                    position=int(row['pos']),
                    team=row['team'],
                    played=int(row['pld']),
                    won=int(row['w']),
                    drawn=int(row['d']),
                    lost=int(row['l']),
                    goals_for=int(row['gf']),
                    goals_against=int(row['ga']),
                    goal_difference=int(row['gd']),
                    points=int(row['pts']),
                    uploaded_by=request.user
                )
                standings_to_create.append(standing)
            
            # Bulk create for efficiency
            Standing.objects.bulk_create(standings_to_create)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully uploaded standings for season {season}',
                'season': season
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing CSV file: {str(e)}'
            }, status=400)
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid form data',
            'errors': form.errors
        }, status=400)


@login_required
@csrf_exempt
@require_POST
def upload_standings_flutter(request):
    """
    Flutter helper endpoint to upload standings using CSV content (string).

    The web page uses multipart upload with a file input. On Flutter, it's
    simpler and more reliable to pick a .csv file, read it as text, then send
    `csv_content` and `season` in a normal POST body.
    """
    if not request.user.is_superuser:
        return JsonResponse(
            {
                "status": "error",
                "message": "Only superusers can upload standings data",
            },
            status=403,
        )

    season = (request.POST.get("season") or "").strip()
    csv_content = (request.POST.get("csv_content") or "").lstrip("\ufeff")

    if not season:
        return JsonResponse(
            {"status": "error", "message": "Season is required."}, status=400
        )

    allowed_seasons = {choice[0] for choice in Standing.SEASON_CHOICES}
    if season not in allowed_seasons:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Invalid season '{season}'. Allowed: {', '.join(sorted(allowed_seasons))}.",
            },
            status=400,
        )

    if not csv_content.strip():
        return JsonResponse(
            {"status": "error", "message": "CSV content is required."}, status=400
        )

    required_headers = {
        "pos",
        "team",
        "pld",
        "w",
        "d",
        "l",
        "gf",
        "ga",
        "gd",
        "pts",
    }

    try:
        io_string = io.StringIO(csv_content)
        reader = csv.DictReader(io_string)
        raw_headers = reader.fieldnames or []
        headers = {h.strip().lower() for h in raw_headers if h}

        if not required_headers.issubset(headers):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "CSV header must include: "
                    + ", ".join(sorted(required_headers)),
                },
                status=400,
            )

        standings_to_create = []
        seen_positions = set()

        row_index = 1  # header row
        for row in reader:
            row_index += 1
            normalized = {
                (k or "").strip().lower(): (v or "").strip()
                for k, v in (row or {}).items()
            }

            # Skip empty lines (common at the end of CSV exports)
            if not any(normalized.values()):
                continue

            try:
                position = int(normalized.get("pos") or "0")
            except ValueError:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Invalid 'pos' at row {row_index}.",
                    },
                    status=400,
                )

            if not (1 <= position <= 20):
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Position must be between 1 and 20 (row {row_index}).",
                    },
                    status=400,
                )

            if position in seen_positions:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Duplicate position {position} in CSV (row {row_index}).",
                    },
                    status=400,
                )
            seen_positions.add(position)

            team = normalized.get("team") or ""
            if not team:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Missing 'team' at row {row_index}.",
                    },
                    status=400,
                )

            def parse_int(key: str) -> int:
                try:
                    return int(normalized.get(key) or "0")
                except ValueError:
                    raise ValueError(f"Invalid '{key}' at row {row_index}.")

            played = parse_int("pld")
            won = parse_int("w")
            drawn = parse_int("d")
            lost = parse_int("l")
            goals_for = parse_int("gf")
            goals_against = parse_int("ga")
            goal_difference = parse_int("gd")
            points = parse_int("pts")

            standings_to_create.append(
                Standing(
                    season=season,
                    position=position,
                    team=team,
                    played=played,
                    won=won,
                    drawn=drawn,
                    lost=lost,
                    goals_for=goals_for,
                    goals_against=goals_against,
                    goal_difference=goal_difference,
                    points=points,
                    uploaded_by=request.user,
                )
            )

        if not standings_to_create:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "CSV has no data rows.",
                },
                status=400,
            )

        with transaction.atomic():
            Standing.objects.filter(season=season).delete()
            Standing.objects.bulk_create(standings_to_create)

        return JsonResponse(
            {
                "status": "success",
                "message": f"Successfully uploaded standings for season {season}",
                "season": season,
            }
        )

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Error processing CSV content: {str(e)}",
            },
            status=400,
        )

def get_available_seasons(request):
    """Get list of seasons that have data uploaded"""
    seasons = Standing.objects.values_list('season', flat=True).distinct().order_by('season')
    return JsonResponse({'seasons': list(seasons)})


@staff_member_required
def check_admin_status(request):
    return JsonResponse({"is_staff": True})


def _parse_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            return {}
    return request.POST.dict()


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


@staff_member_required
@csrf_exempt
@require_POST
def create_standing_api(request):
    payload = _parse_payload(request)

    season = (payload.get('season') or '').strip()
    team = (payload.get('team') or '').strip()

    standing = Standing(
        season=season,
        position=_to_int(payload.get('position')),
        team=team,
        played=_to_int(payload.get('played')),
        won=_to_int(payload.get('won')),
        drawn=_to_int(payload.get('drawn')),
        lost=_to_int(payload.get('lost')),
        goals_for=_to_int(payload.get('goals_for')),
        goals_against=_to_int(payload.get('goals_against')),
        goal_difference=_to_int(payload.get('goals_for')) - _to_int(payload.get('goals_against')),
        points=_to_int(payload.get('points')),
        uploaded_by=request.user,
    )

    try:
        standing.full_clean()
        standing.save()
    except ValidationError as e:
        return JsonResponse(
            {'status': 'error', 'message': 'Validation failed', 'errors': e.message_dict},
            status=400,
        )
    except IntegrityError:
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Position already exists for this season.',
                'errors': {'position': ['This position is already used for the selected season.']},
            },
            status=400,
        )

    return JsonResponse(
        {
            'status': 'success',
            'message': 'Standing created successfully.',
            'standing': {
                'id': standing.id,
                'season': standing.season,
                'position': standing.position,
                'team': standing.team,
                'played': standing.played,
                'won': standing.won,
                'drawn': standing.drawn,
                'lost': standing.lost,
                'goals_for': standing.goals_for,
                'goals_against': standing.goals_against,
                'goal_difference': standing.goal_difference,
                'points': standing.points,
            },
        }
    )


@staff_member_required
@csrf_exempt
@require_POST
def edit_standing_api(request, pk):
    standing = Standing.objects.filter(pk=pk).first()
    if not standing:
        return JsonResponse({'status': 'error', 'message': 'Standing not found.'}, status=404)

    payload = _parse_payload(request)

    standing.season = (payload.get('season') or standing.season).strip()
    standing.position = _to_int(payload.get('position'), standing.position)
    standing.team = (payload.get('team') or standing.team).strip()
    standing.played = _to_int(payload.get('played'), standing.played)
    standing.won = _to_int(payload.get('won'), standing.won)
    standing.drawn = _to_int(payload.get('drawn'), standing.drawn)
    standing.lost = _to_int(payload.get('lost'), standing.lost)
    standing.goals_for = _to_int(payload.get('goals_for'), standing.goals_for)
    standing.goals_against = _to_int(payload.get('goals_against'), standing.goals_against)
    standing.goal_difference = standing.goals_for - standing.goals_against
    standing.points = _to_int(payload.get('points'), standing.points)

    try:
        standing.full_clean()
        standing.save()
    except ValidationError as e:
        return JsonResponse(
            {'status': 'error', 'message': 'Validation failed', 'errors': e.message_dict},
            status=400,
        )
    except IntegrityError:
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Position already exists for this season.',
                'errors': {'position': ['This position is already used for the selected season.']},
            },
            status=400,
        )

    return JsonResponse(
        {
            'status': 'success',
            'message': 'Standing updated successfully.',
            'standing': {
                'id': standing.id,
                'season': standing.season,
                'position': standing.position,
                'team': standing.team,
                'played': standing.played,
                'won': standing.won,
                'drawn': standing.drawn,
                'lost': standing.lost,
                'goals_for': standing.goals_for,
                'goals_against': standing.goals_against,
                'goal_difference': standing.goal_difference,
                'points': standing.points,
            },
        }
    )


@staff_member_required
@csrf_exempt
@require_POST
def delete_standing_api(request, pk):
    standing = Standing.objects.filter(pk=pk).first()
    if not standing:
        return JsonResponse({'status': 'error', 'message': 'Standing not found.'}, status=404)

    standing.delete()
    return JsonResponse({'status': 'success', 'message': 'Standing deleted successfully.'})


@staff_member_required
@csrf_exempt
@require_POST
def clear_season_api(request):
    payload = _parse_payload(request)
    season = (payload.get('season') or '').strip()

    if not season:
        return JsonResponse(
            {'status': 'error', 'message': 'Season is required.'}, status=400
        )

    deleted_count, _ = Standing.objects.filter(season=season).delete()
    return JsonResponse(
        {
            'status': 'success',
            'message': f'Deleted {deleted_count} standings for season {season}.',
            'deleted': deleted_count,
        }
    )
