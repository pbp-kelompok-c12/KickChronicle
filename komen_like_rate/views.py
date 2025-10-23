# komen_like_rate/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Rating, Comment, Favorite
from .forms import RatingForm, CommentForm
from django.views.decorators.http import require_POST
from highlight.models import Highlight 
from django.http import JsonResponse, HttpResponseForbidden


 

@login_required
def add_comment(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.highlight = highlight
            comment.save()
            data = {
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Invalid form'}, status=400)
    return HttpResponseBadRequest("Invalid request")

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
    try:
        highlight_id = UUID(request.POST.get("highlight_id", ""))
        rating_value = int(request.POST.get("rating", 0))
        if rating_value < 1 or rating_value > 5:
            raise ValueError()
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

    highlight = get_object_or_404(Highlight, id=highlight_id)

    rating, created = Rating.objects.get_or_create(
        user=request.user,
        highlight=highlight,
        defaults={'value': rating_value}
    )
    if not created:
        rating.value = rating_value
        rating.save()

    return JsonResponse({'status': 'success', 'rating': rating.value})
    
def top_rated(request):
    from django.db.models import Avg
    from highlight.models import Highlight

    highlights = Highlight.objects.all()
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    if start:
        highlights = highlights.filter(created_at__date__gte=start)
    if end:
        highlights = highlights.filter(created_at__date__lte=end)
    highlights = highlights.annotate(avg_rating=Avg('rating__value')).order_by('-avg_rating')[:10]
    
    return render(request, 'komen_like_rate/top_rated.html', {
        'highlights': highlights,
        'start_date': start,
        'end_date': end,
    })

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
        highlight__isnull=False  # hanya favorit yang masih punya highlight
    ).select_related('highlight')

    return render(request, 'komen_like_rate/favorites.html', {
        'favorites': favorites
    })
