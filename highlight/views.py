from django.shortcuts import get_object_or_404, redirect, render
from highlight.models import Highlight
# kemungkinan import dari tim
# kemungkinan import dari komen_like_rate

def show_highlight(request,id):
    highlight = get_object_or_404(Highlight,pk=id)
    context = {
        'highlight': highlight
    }

    return render(request, "highlight_detail.html", context)

# def rate_higlight

# def 

