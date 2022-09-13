from rest_framework.response import Response


def healthcheck(request, *args, **kwargs):
    return Response()
