from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    context_dict = {'boldmessage': "A fuegoooo"}
    return render(request, 'tfgWeb/index.html', context=context_dict)