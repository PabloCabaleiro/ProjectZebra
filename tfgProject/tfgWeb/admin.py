from django.contrib import admin
from tfgWeb.models import Image, Serie, Atlas, AtlasImage, MuestraAtlas, Muestra, UserProfile

admin.site.register(Serie)
admin.site.register(Muestra)
admin.site.register(Image)
admin.site.register(Atlas)
admin.site.register(MuestraAtlas)
admin.site.register(AtlasImage)
admin.site.register(UserProfile)
