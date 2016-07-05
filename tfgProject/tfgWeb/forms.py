from django import forms
from tfgWeb.models import UserProfile
from django.contrib.auth.models import User
from tfgWeb import utils

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
    atlas = forms.CharField(widget=forms.Select)
    serie = forms.CharField(widget=forms.Select)
    muestra = forms.CharField(widget=forms.Select)
    time = forms.IntegerField(widget=forms.NumberInput)
    class Meta:
        fields = ('pos_x','pos_y','pos_z','serie', 'time')

class UploadForm(forms.Form):
    file = forms.FileField(label='Select a .lif file')
    class Meta:
        fields = ('file',)