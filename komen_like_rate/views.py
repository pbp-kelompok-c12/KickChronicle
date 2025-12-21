# komen_like_rate/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.templatetags.static import static
from django.db.models.functions import Coalesce
from django.db import transaction
from .models import Rating, Comment, Favorite
from .forms import RatingForm, CommentForm
from django.views.decorators.http import require_POST
from highlight.models import Highlight
import logging
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__) 
import json
from datetime import date
from django.utils.dateparse import parse_date

@login_required
def add_comment(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id)

    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request")

    form = CommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form'}, status=400)

    comment = form.save(commit=False)
    comment.user = request.user
    comment.highlight = highlight
    comment.save()

    avatar_url = ""
    try:
        prof = getattr(request.user, "profile", None)
        if prof and prof.image:
            avatar_url = prof.image.url
    except Exception:
        avatar_url = ""

    data = {
        'status': 'ok',
        'id': comment.id,
        'user': comment.user.username,
        'content': comment.content,
        'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        'avatar_url': avatar_url,
        'initial': comment.user.username[:1].upper(),
    }
    return JsonResponse(data)

@login_required
def toggle_favorite(request, highlight_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

    highlight = get_object_or_404(Highlight, id=highlight_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, highlight=highlight)

    if created:
        action = "added"
        favorited = True
    else:
        fav.delete()
        action = "removed"
        favorited = False

    return JsonResponse({"status": "ok", "action": action, "favorited": favorited})

@login_required
@require_POST
def submit_rating(request):
    from uuid import UUID
    user_id = request.user.id
    logger.info(f"User {user_id} attempting to submit rating.")

    try:
        highlight_id = UUID(request.POST.get("highlight_id", ""))
        rating_value = int(request.POST.get("rating", 0))
        if not 1 <= rating_value <= 5:
            logger.warning(f"User {user_id} submitted invalid rating value: {rating_value}")
            raise ValueError("Rating out of bounds")
    except Exception as e:
        logger.error(f"Invalid data from user {user_id}. Error: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    logger.info(f"Data validated for user {user_id}, highlight {highlight_id}, rating {rating_value}.")

    highlight = get_object_or_404(Highlight, id=highlight_id)
    try:
        with transaction.atomic():
            rating, created = Rating.objects.get_or_create(
                user=request.user,
                highlight=highlight,
                defaults={'value': rating_value}
            )
            if not created:
                rating.value = rating_value
                rating.save(update_fields=['value'])
                logger.info(f"SUCCESS: Rating updated for highlight {highlight_id} by user {user_id} to {rating_value}")
            else:
                logger.info(f"SUCCESS: Rating created for highlight {highlight_id} by user {user_id} with value {rating_value}")

    except Exception as e:
        logger.error(f"DATABASE ERROR for user {user_id} on highlight {highlight_id}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Failed to save rating due to a server error.'}, status=500)

    return JsonResponse({'status': 'success', 'rating': rating.value})
    
def top_rated(request):
    highlights = Highlight.objects.all()
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    if start:
        highlights = highlights.filter(created_at__date__gte=start)
    if end:
        highlights = highlights.filter(created_at__date__lte=end)

    highlights = highlights.annotate(
        avg_rating=Coalesce(Avg('rating__value'), 0.0)
    ).order_by('-avg_rating')[:10]

    return render(request, 'komen_like_rate/top_rated.html', {
        'highlights': highlights,
        'start_date': start,
        'end_date': end,
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user_id != request.user.id:
        return HttpResponseForbidden("Tidak boleh menghapus komentar orang lain.")
    comment.delete()
    return JsonResponse({"status": "ok", "id": comment_id})

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(
        user=request.user,
        highlight__isnull=False
    ).select_related('highlight')

    return render(request, 'komen_like_rate/favorites.html', {
        'favorites': favorites
    })

@login_required
@csrf_exempt
def get_comments_mobile(request, highlight_id):
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "Invalid method"}, status=405)

    highlight = get_object_or_404(Highlight, id=highlight_id)
    
    comments = Comment.objects.filter(
        highlight=highlight
    ).select_related("user").order_by('-created_at')

    data = []
    for c in comments:
        profile = getattr(c.user, "profile", None)

        if profile and profile.image:
            avatar_url = profile.image.url
            if not avatar_url.startswith('http'):
                avatar_url = request.build_absolute_uri(avatar_url)
        else:
            avatar_url = request.build_absolute_uri(static("img/default.png"))

        if avatar_url.startswith('http:'):
            avatar_url = avatar_url.replace('http:', 'https:', 1)

        data.append({
            "id": c.id,
            "user": c.user.username,
            "content": c.content,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "avatar": avatar_url,
            "is_owner": c.user_id == request.user.id,
        })

    return JsonResponse({"status": True, "comments": data})

@login_required
@csrf_exempt
def add_comment_mobile(request, highlight_id):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Invalid method"}, status=405)

    data = json.loads(request.body.decode('utf-8'))
    content = data.get('content')

    if not content:
        return JsonResponse({"status": False, "message": "Content required"}, status=400)

    highlight = get_object_or_404(Highlight, id=highlight_id)
    comment = Comment.objects.create(
        user=request.user,
        highlight=highlight,
        content=content
    )

    return JsonResponse({
        "status": True,
        "id": comment.id,
        "content": comment.content,
        "user": request.user.username,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })


@login_required
@csrf_exempt
def toggle_favorite_mobile(request, highlight_id):
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "Invalid method"}, status=405)

    highlight = get_object_or_404(Highlight, id=highlight_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, highlight=highlight)

    if created:
        return JsonResponse({"status": True, "favorited": True})
    else:
        fav.delete()
        return JsonResponse({"status": True, "favorited": False})


@login_required
@csrf_exempt
def submit_rating_mobile(request):
    from uuid import UUID

    try:
        data = json.loads(request.body.decode("utf-8"))
        highlight_id = UUID(str(data.get("highlight_id", "")))
        rating_value = int(data.get("rating", 0))

        if not (1 <= rating_value <= 5):
            return JsonResponse({"status": False, "message": "Rating must be 1–5"}, status=400)

    except Exception as e:
        return JsonResponse({"status": False, "message": f"Invalid data: {e}"}, status=400)

    highlight = get_object_or_404(Highlight, id=highlight_id)

    try:
        with transaction.atomic():
            rating, created = Rating.objects.get_or_create(
                user=request.user,
                highlight=highlight,
                defaults={"value": rating_value}
            )

            if not created:
                rating.value = rating_value
                rating.save(update_fields=["value"])

    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": f"Database error: {e}"
        }, status=500)

    avg_rating = Rating.objects.filter(highlight=highlight).aggregate(
        avg=Coalesce(Avg("value"), 0.0)
    )["avg"]

    return JsonResponse({
        "status": True,
        "rating": rating.value,
        "avg_rating": float(avg_rating),
        "highlight": {
            "id": str(highlight.id),
            "name": highlight.name,
            "description": highlight.description,
            "thumbnail": highlight.manual_thumbnail_url,
            "url": highlight.url,
            "season": highlight.season,
            "created_at": highlight.created_at.isoformat(),
        }
    })

@login_required
@csrf_exempt
def delete_comment_mobile(request, comment_id):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Invalid method"}, status=405)

    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)

    comment.delete()

    return JsonResponse({"status": True, "message": "Comment deleted"})

@login_required
@csrf_exempt
@login_required
@csrf_exempt
@login_required
@csrf_exempt
def favorite_list_mobile(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related("highlight")

    data = []

    for fav in favorites:
        hl = fav.highlight
        
        home_standing = None
        if hl.home:
            home_standing = {
                "team": hl.home.team,
                "played": hl.home.played,
                "won": hl.home.won,
                "drawn": hl.home.drawn,
                "lost": hl.home.lost,
            }

        away_standing = None
        if hl.away:
            away_standing = {
                "team": hl.away.team,
                "played": hl.away.played,
                "won": hl.away.won,
                "drawn": hl.away.drawn,
                "lost": hl.away.lost,
            }

        data.append({
            "id": hl.pk,
            "name": hl.name,
            "url": hl.url,
            "description": hl.description,
            "season": hl.season,
            "manual_thumbnail_url": hl.manual_thumbnail_url,
            "created_at": hl.created_at.isoformat(),
            "home_standing": home_standing,
            "away_standing": away_standing,
        })

    return JsonResponse({"status": True, "favorites": data})


@login_required
@csrf_exempt
def get_user_rating_mobile(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id)

    rating = Rating.objects.filter(
        user=request.user,
        highlight=highlight
    ).first()

    return JsonResponse({
        "status": True,
        "rating": rating.value if rating else None
    })



@csrf_exempt
def top_rated_mobile(request):
    highlights = Highlight.objects.all()

    start = request.GET.get("start_date")
    end = request.GET.get("end_date")

    if start:
        highlights = highlights.filter(created_at__date__gte=start)
    if end:
        highlights = highlights.filter(created_at__date__lte=end)

    highlights = highlights.annotate(
        avg_rating=Coalesce(Avg('rating__value'), 0.0)
    ).order_by('-avg_rating')

    data = []

    for highlight in highlights:

        # HOME STANDING
        home_standing = None
        if highlight.home:
            home_standing = {
                "team": highlight.home.team,
                "played": highlight.home.played,
                "won": highlight.home.won,
                "drawn": highlight.home.drawn,
                "lost": highlight.home.lost,
            }

        # AWAY STANDING
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
            "title": highlight.name,  # untuk mobile
            "url": highlight.url,
            "description": highlight.description,
            "season": highlight.season,
            "manual_thumbnail_url": highlight.manual_thumbnail_url,
            "created_at": highlight.created_at.isoformat(),
            "avg_rating": float(highlight.avg_rating),
            "home_standing": home_standing,
            "away_standing": away_standing,
        })

    return JsonResponse({
        "status": True,
        "count": len(data),
        "start_date": start,
        "end_date": end,
        "highlights": data
    })