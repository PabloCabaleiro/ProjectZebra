from django.contrib import admin
from tfgWeb.models import Image, Galery, UserProfile, Axis, Experiment

admin.site.register(Galery)
admin.site.register(Image)
admin.site.register(Axis)
admin.site.register(UserProfile)
admin.site.register(Experiment)