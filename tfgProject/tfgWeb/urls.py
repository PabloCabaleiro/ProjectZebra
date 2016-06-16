from django.conf.urls import url
from tfgWeb import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
