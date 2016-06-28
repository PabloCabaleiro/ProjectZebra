from django import forms
from tfgWeb.models import UserProfile
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('organization',)

class InfoForm(forms.Form):
    pos_x = forms.IntegerField(max_value=1024)
    pos_y = forms.IntegerField(max_value=1024)
    pos_z = forms.IntegerField(max_value=1024)
    serie = forms.CharField(widget=forms.Select)
    time = forms.IntegerField(widget=forms.NumberInput)
    class Meta:
        fields = ('pos_x','pos_y','pos_z','serie', 'time')