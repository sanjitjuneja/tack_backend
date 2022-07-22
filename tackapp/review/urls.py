from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"reviews", ReviewViewset)

urlpatterns = router.urls
