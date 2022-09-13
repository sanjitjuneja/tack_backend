from django.http import HttpResponse


def healthcheck(request, *args, **kwargs):
    return HttpResponse('')
