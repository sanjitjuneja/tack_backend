from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"groups", GroupViewset)

urlpatterns = router.urls
