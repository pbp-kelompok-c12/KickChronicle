from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, EditProfileForm, CustomPasswordChangeForm, UserUpdateForm, ProfileUpdateForm
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.http import require_http_methods
from django.utils.datastructures import MultiValueDictKeyError
import json

def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registrasi berhasil. Selamat datang!")
            return redirect('auth_profil:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Anda berhasil login sebagai {username}.")
                return redirect('highlight:show_main_page')
            else:
                messages.error(request, "Username atau password salah.")
        else:
            messages.error(request, "Username atau password salah.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, "Anda berhasil logout.")
    return redirect('auth_profil:login')

@login_required
def profile_view(request):
    edit_form = EditProfileForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    has_password = request.user.has_usable_password()
    context = {
        'edit_form': edit_form,
        'password_change_form': password_form,
        'has_password': has_password
    }
    return render(request, 'profile.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()

            new_url = ''
            try:
                if request.user.profile.image:
                    new_url = request.user.profile.image.url
            except Exception:
                new_url = ''

            return JsonResponse({
                'status': 'success',
                'message': 'Profil berhasil diperbarui!',
                'new_image_url': new_url,
            })

        errors = {}
        errors.update(u_form.errors.get_json_data())
        errors.update(p_form.errors.get_json_data())
        return JsonResponse({'status': 'error', 'errors': errors}, status=400)

    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=request.user.profile)

    if getattr(request.user.profile, "image", None):
        try:
            current_avatar_url = request.user.profile.image.url
        except Exception:
            current_avatar_url = static('img/default.png')
    else:
        current_avatar_url = static('img/default.png')

    return render(
        request, 'edit_profile.html',
        {'u_form': u_form, 'p_form': p_form, 'current_avatar_url': current_avatar_url}
    )

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('/')
    return render(request, 'delete_account_confirm.html')

@login_required
@require_POST
def password_change_view(request):
    form = CustomPasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"status": "success", "message": "Password updated successfully!"})
    return JsonResponse({"status": "error", "errors": form.errors}, status=400)