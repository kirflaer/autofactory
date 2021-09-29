from django.shortcuts import render
from datetime import datetime as dt, date as date_construct
import time
from .models import Organization


def index(request):
    # start_time = time.time()
    # start = dt.now()
    #
    # f = open("E:/load.txt", "r")
    # f_line = ""
    # for line in f:
    #     Organization.objects.create(ext_key=line[:36])
    #
    # f.close()
    # end = dt.now()

    return render(request, 'index.html')
