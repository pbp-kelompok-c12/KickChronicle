from django.shortcuts import get_object_or_404, redirect, render
from highlight.models import Highlight
from highlight.forms import HighlightForm

# kemungkinan import dari tim
# kemungkinan import dari komen_like_rate

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

def show_highlight(request,id):
    highlight = get_object_or_404(Highlight,pk=id)
    context = {
        'highlight': highlight
    }

    return render(request, "highlight_detail.html", context)

# def rate_higlight

def add_highlight(request):
    form = HighlightForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        highlight_entry = form.save(commit = False)
        # product_entry.user = request.user
        highlight_entry.save()
        return redirect('highlight:show_main_page')

    context = {'form': form}
    return render(request, "add_highlight.html", context)

def edit_highlight(request, id):
    highlight = get_object_or_404(Highlight, pk=id)
    form = HighlightForm(request.POST or None, instance=highlight)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('highlight:show_main_page')
    
    context = {
        'form': form
    }

    return render(request, "edit_highlight.html", context)

