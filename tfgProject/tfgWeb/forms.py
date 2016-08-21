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
    zone = forms.CharField()
    atlas = forms.CharField(widget=forms.Select)
    serie = forms.CharField(widget=forms.Select)
    time = forms.IntegerField(widget=forms.NumberInput)
    width = forms.IntegerField(max_value=1024)
    height = forms.IntegerField(max_value=1024)
    depth = forms.IntegerField(max_value=1024)
    pos_x_start = forms.IntegerField(max_value=1024)
    pos_y_start = forms.IntegerField(max_value=1024)
    pos_z_start = forms.IntegerField(max_value=1024)
    vista = forms.CharField()

    class Meta:
        fields = ('pos_x','pos_y','pos_z','serie', 'time')

#Index view
class UploadForm(forms.Form):
    file = forms.FileField(label='Select a .lif file')
    order = forms.CharField(max_length=4)
    class Meta:
        fields = ('file',)

#Choose zone forms
class ZoneForm(forms.Form):
    name = forms.CharField(max_length=128)
    atlas = forms.CharField()
    max_x = forms.IntegerField()
    min_x = forms.IntegerField()
    max_y = forms.IntegerField()
    min_y = forms.IntegerField()
    max_z = forms.IntegerField()
    min_z = forms.IntegerField()

    class Meta:
        fields = ('name', 'atlas', 'max_x','min_x','max_y','min_y','max_z','min_z')

class ZoneInfoForm(forms.Form):
    atlas = forms.CharField()
    max_x = forms.IntegerField()
    min_x = forms.IntegerField()
    max_y = forms.IntegerField()
    min_y = forms.IntegerField()
    max_z = forms.IntegerField()
    min_z = forms.IntegerField()
    pos_x = forms.IntegerField()
    pos_y = forms.IntegerField()
    pos_z = forms.IntegerField()
    class Meta:
        fields = ('atlas','max_x','min_x','max_y','min_y','max_z','min_z', 'pos_x', 'pos_y', 'pos_z')

#Atlas view
class AtlasForm(forms.Form):
    atlas = forms.CharField();
    pos_x = forms.IntegerField();
    pos_y = forms.IntegerField();
    pos_z = forms.IntegerField();
    zone = forms.CharField();
    vista = forms.CharField();

    class Meta:
        fields = ('atlas', 'pos_x', 'pos_y', 'pos_z', 'zone', 'vista')