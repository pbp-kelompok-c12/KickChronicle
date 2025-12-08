from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.templatetags.static import static
from django.utils.text import slugify
import csv
import io
from .models import Standing
from .forms import StandingUploadForm

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

def get_available_seasons(request):
    """Get list of seasons that have data uploaded"""
    seasons = Standing.objects.values_list('season', flat=True).distinct().order_by('season')
    return JsonResponse({'seasons': list(seasons)})
