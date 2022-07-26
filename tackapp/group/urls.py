from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"groups", GroupViewset)
router.register(r"invites", InvitesView)

urlpatterns = router.urls
