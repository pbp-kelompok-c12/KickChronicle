from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import requests
from .forms import CustomUserCreationForm, EditProfileForm, CustomPasswordChangeForm, UserUpdateForm, ProfileUpdateForm
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.http import require_http_methods
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from django.utils.crypto import get_random_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile
import base64
from django.core.files.base import ContentFile

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

@csrf_exempt
def login_flutter(request):
    if request.method == 'POST':
        # COBA BACA DARI JSON (request.body) DULU
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # JIKA GAGAL (KARENA FLUTTER KIRIM FORM DATA), AMBIL DARI request.POST
            data = request.POST
        
        # Ambil data dengan .get() agar aman
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                "status": True,
                "message": "Login berhasil!",
                "username": username,
            }, status=200)
        else:
            return JsonResponse({
                "status": False,
                "message": "Username atau password salah.",
            }, status=401)
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def register_flutter(request):
    if request.method == 'POST':
        # LAKUKAN HAL SAMA UNTUK REGISTER
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        username = data.get('username')
        password = data.get('password')
        password_confirm = data.get('passwordConfirm')

        if not username or not password or not password_confirm:
             return JsonResponse({"status": False, "message": "Semua field harus diisi"}, status=400)

        if password != password_confirm:
            return JsonResponse({"status": False, "message": "Password tidak cocok"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": False, "message": "Username sudah digunakan"}, status=409)

        user = User.objects.create_user(username=username, password=password)
        user.save()

        return JsonResponse({"status": True, "message": "Akun berhasil dibuat!"}, status=201)
    
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

@csrf_exempt
def logout_flutter(request):
    logout(request)
    return JsonResponse({"status": True, "message": "Logout berhasil!"}, status=200)

@csrf_exempt
def google_login_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            # 1. AMBIL URL FOTO DARI GOOGLE (Pastikan Flutter mengirim key 'photoUrl')
            photo_url = data.get('photoUrl') 

            if not email:
                return JsonResponse({'status': False, 'message': 'Email diperlukan'}, status=400)

            user = User.objects.filter(email=email).first()

            if not user:
                # Buat User Baru
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User.objects.create_user(username=username, email=email)
                user.set_unusable_password()
                user.save()

            # 2. LOGIKA SIMPAN FOTO GOOGLE (Untuk User Baru / Lama yg belum ada foto)
            if user and photo_url:
                profile, created = Profile.objects.get_or_create(user=user)
                
                # Cek jika profile belum punya gambar (masih kosong/default)
                if not profile.image:
                    try:
                        # Download gambar dari URL Google
                        response = requests.get(photo_url)
                        if response.status_code == 200:
                            # Simpan ke field image
                            file_name = f"{user.username}_google_avatar.jpg"
                            profile.image.save(file_name, ContentFile(response.content), save=True)
                    except Exception as e:
                        print(f"Gagal menyimpan foto profil Google: {e}")

            # Login User
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Ambil URL foto terbaru untuk dikirim balik ke Flutter
            final_photo_url = ""
            if hasattr(user, 'profile') and user.profile.image:
                final_photo_url = user.profile.image.url
                if not final_photo_url.startswith('http'):
                    final_photo_url = request.build_absolute_uri(final_photo_url)
                if final_photo_url.startswith('http:'):
                    final_photo_url = final_photo_url.replace('http:', 'https:', 1)

            return JsonResponse({
                'status': True, 
                'message': 'Login Google berhasil', 
                'username': user.username,
                'photoUrl': final_photo_url,
            })

        except Exception as e:
            print(f"Error Google Login: {e}")
            return JsonResponse({'status': False, 'message': f'Server Error: {str(e)}'}, status=500)

    return JsonResponse({'status': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def register_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        username = data.get('username')
        email = data.get('email')  # Ambil email
        password = data.get('password')
        password_confirm = data.get('passwordConfirm')

        # 1. Validasi Input Kosong
        if not username or not email or not password or not password_confirm:
            return JsonResponse({"status": False, "message": "Semua field harus diisi"}, status=400)

        # 2. Validasi Password Match
        if password != password_confirm:
            return JsonResponse({"status": False, "message": "Password tidak cocok"}, status=400)

        # 3. Validasi Unik Username
        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": False, "message": "Username sudah digunakan"}, status=409)

        # 4. Validasi Unik Email (BARU)
        if User.objects.filter(email=email).exists():
            return JsonResponse({"status": False, "message": "Email sudah terdaftar. Silakan login."}, status=409)

        # 5. Validasi Password Standard Django (BARU - Sesuai Foto)
        # Kita buat user sementara (belum disimpan) untuk validasi password
        # agar validator bisa mengecek kemiripan dengan username/email
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError as e:
            # Mengambil pesan error pertama dari list error Django
            return JsonResponse({"status": False, "message": e.messages[0]}, status=400)

        # 6. Buat User jika semua lolos
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        return JsonResponse({"status": True, "message": "Akun berhasil dibuat!"}, status=201)
    
    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)

def check_superuser(request):
    if request.user.is_authenticated:
        return JsonResponse({
            "status": True,
            "username": request.user.username,
            "is_superuser": request.user.is_superuser
        }, status=200)
    
    return JsonResponse({
        "status": False,
        "is_superuser": False,
        "message": "User not authenticated"
    }, status=200)

@csrf_exempt
def get_user_profile(request):
    if request.user.is_authenticated:
        user = request.user
        # Get or Create profile untuk menghindari error jika profile belum ada
        profile, created = Profile.objects.get_or_create(user=user)

        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            # Mengembalikan URL gambar jika ada di database Django
            'image_url': profile.image.url if profile.image else None, 
        }
        return JsonResponse({'status': True, 'data': data}, status=200)
    return JsonResponse({'status': False, 'message': 'Belum login'}, status=401)

@csrf_exempt
def edit_profile_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            user = request.user
            profile = user.profile # Pastikan profile sudah dibuat via signal/get_user_profile

            # 1. Update Data User (Username, Email, Nama)
            new_username = data.get('username')
            new_email = data.get('email')
            
            # Validasi Username Unik (jika berubah)
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({'status': False, 'message': 'Username sudah digunakan.'}, status=400)
                user.username = new_username

            # Validasi Email Unik (jika berubah)
            if new_email and new_email != user.email:
                if User.objects.filter(email=new_email).exists():
                    return JsonResponse({'status': False, 'message': 'Email sudah digunakan.'}, status=400)
                user.email = new_email

            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.save()

            # 2. Update Foto Profil (Base64)
            image_data = data.get('image')
            if image_data:
                # Format base64 dari flutter biasanya raw string, tapi kadang ada prefix data:image/...
                if ";" in image_data:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                else:
                    imgstr = image_data
                    ext = "png" # Default extension

                data_img = ContentFile(base64.b64decode(imgstr), name=f'{user.username}_avatar.{ext}')
                profile.image = data_img
                profile.save()

            return JsonResponse({'status': True, 'message': 'Profil berhasil diperbarui!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def change_password_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            # CustomPasswordChangeForm membutuhkan user sebagai argumen pertama
            form = CustomPasswordChangeForm(user=request.user, data=data)
            
            if form.is_valid():
                user = form.save()
                # Penting: Update session agar user tidak ter-logout otomatis setelah ganti password
                update_session_auth_hash(request, user)
                return JsonResponse({"status": True, "message": "Password berhasil diubah!"}, status=200)
            else:
                # Mengambil error pertama dari form
                error_msg = next(iter(form.errors.values()))[0]
                return JsonResponse({"status": False, "message": error_msg}, status=400)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    return JsonResponse({"status": False, "message": "Method not allowed atau belum login"}, status=401)

@csrf_exempt
def delete_account_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            user = request.user
            user.delete() # Menghapus user dan profil terkait (Cascade)
            logout(request)
            return JsonResponse({"status": True, "message": "Akun berhasil dihapus."}, status=200)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
    
    return JsonResponse({"status": False, "message": "Method not allowed atau belum login"}, status=401)

@csrf_exempt
def password_reset_request_flutter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # PasswordResetForm bawaan Django mengharapkan dict dengan key 'email'
            form = PasswordResetForm(data)
            
            if form.is_valid():
                # Opsi: email_template_name bisa disesuaikan jika ingin format khusus
                # form.save() akan mengirimkan email secara otomatis sesuai setting SMTP Django Anda
                # use_https=request.is_secure() memastikan link di email protokolnya benar
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name='password_reset_email.html', # Template bawaan auth_profil Anda
                )
                
                return JsonResponse({
                    "status": True, 
                    "message": "Jika email terdaftar, link reset password telah dikirim."
                }, status=200)
            else:
                return JsonResponse({"status": False, "message": "Format email tidak valid."}, status=400)
        
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    return JsonResponse({"status": False, "message": "Method not allowed"}, status=405)