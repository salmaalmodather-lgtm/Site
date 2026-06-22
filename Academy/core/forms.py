from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Teacher


INPUT_CLASSES = (
    "w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-100 "
    "focus:outline-none focus:border-indigo-500 transition-all placeholder:text-slate-600"
)


class SignUpForm(forms.Form):
    """فورم تسجيل مبسط: email + password فقط — username بيتولّد أوتوماتيك"""
    email    = forms.EmailField(required=True, label="البريد الإلكتروني")
    password = forms.CharField(required=True, label="كلمة المرور", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد الإلكتروني مسجل بالفعل")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages[0])
        return password

    def save(self):
        email    = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        # توليد username فريد من الـ email
        base = email.split("@")[0][:30]
        username, counter = base, 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(username=username, email=email, password=password)
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": INPUT_CLASSES})


class TeacherForm(forms.ModelForm):
    class Meta:
        model   = Teacher
        fields  = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "مثال: مستر أكرم",
                "class": INPUT_CLASSES,
            })
        }
        labels = {"name": "اسم المستر / المعلم"}


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "اسم المستخدم"
        self.fields["password"].label = "كلمة المرور"
        for field in self.fields.values():
            field.widget.attrs.update({"class": INPUT_CLASSES})