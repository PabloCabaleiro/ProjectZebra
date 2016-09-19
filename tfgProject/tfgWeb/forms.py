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

#Experiment view
class InfoForm(forms.Form):
    pos_x = forms.IntegerField(max_value=1024)
    pos_y = forms.IntegerField(max_value=1024)
    pos_z = forms.IntegerField(max_value=1024)
    pos_x_atlas = forms.IntegerField(max_value=1024)
    pos_y_atlas = forms.IntegerField(max_value=1024)
    pos_z_atlas = forms.IntegerField(max_value=1024)
    atlas = forms.CharField(widget=forms.Select)
    serie = forms.CharField(widget=forms.Select)
    time = forms.IntegerField(widget=forms.NumberInput)
    width = forms.IntegerField(max_value=1024)
    height = forms.IntegerField(max_value=1024)
    depth = forms.IntegerField(max_value=1024)
    pos_x_start = forms.IntegerField(max_value=1024)
    pos_y_start = forms.IntegerField(max_value=1024)
    pos_z_start = forms.IntegerField(max_value=1024)
    navigate = forms.IntegerField()
    save = forms.BooleanField()
    view = forms.CharField()

class AtlasForm(forms.Form):
    pos_x = forms.IntegerField(max_value=1024)
    pos_y = forms.IntegerField(max_value=1024)
    pos_z = forms.IntegerField(max_value=1024)
    atlas = forms.CharField(widget=forms.Select)

#Index view
class UploadForm(forms.Form):
    file = forms.FileField(label='Select a .lif file')
    name = forms.CharField()
    top_axis = forms.CharField(max_length=1)
    front_axis = forms.CharField(max_length=1)
    side_axis = forms.CharField(max_length=1)
    class Meta:
        fields = ('file',)

class NameForm(forms.Form):
    name = forms.CharField()

    class Meta:
        fields = ('name',)

class DeleteForm(forms.Form):
    delete = forms.CharField()

    class Meta:
        fields = ('delete',)