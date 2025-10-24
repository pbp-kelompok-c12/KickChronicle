# komen_like_rate/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.db import transaction
from .models import Rating, Comment, Favorite
from .forms import RatingForm, CommentForm
from django.views.decorators.http import require_POST
from highlight.models import Highlight
import logging
logger = logging.getLogger(__name__) 

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