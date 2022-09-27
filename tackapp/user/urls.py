from django.urls import path
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"users", UsersViewset)
urlpatterns = router.urls
