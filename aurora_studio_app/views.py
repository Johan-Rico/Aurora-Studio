from django.shortcuts import render

def home(request):
    return render(request, 'aurora_studio_app/home.html')
