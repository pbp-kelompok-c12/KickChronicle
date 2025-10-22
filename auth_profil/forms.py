from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, PasswordChangeForm
from django import forms
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Sebuah akun dengan alamat email ini sudah ada.")
            
        return email
        
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': '••••••••',
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-700 border border-border text-white placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': '••••••••',
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-700 border border-border text-white placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent'
        })

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Username ini sudah digunakan. Silakan pilih yang lain.")
        return username
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_classes = "w-full px-4 py-3 rounded-lg bg-gray-700 border border-border text-white placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
        self.fields['username'].widget.attrs.update({'class': tailwind_classes})
        self.fields['first_name'].widget.attrs.update({'class': tailwind_classes})
        self.fields['last_name'].widget.attrs.update({'class': tailwind_classes})

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_classes = "w-full px-4 py-3 rounded-lg bg-gray-700 border border-border text-white placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
        
        self.fields['old_password'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'Enter your new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'Confirm your new password'
        })