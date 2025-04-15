from django.shortcuts import render

# Create your views here.

def index(request):
    """ This is the welcome page which the user sees first"""
    return render(request, 'riseup_templates/index.html')