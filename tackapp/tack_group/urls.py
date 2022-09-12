from tack_group.views import GroupViewset, InvitesView
from rest_framework import routers

router = routers.SimpleRouter()
router.register("groups", GroupViewset)
router.register("invites", InvitesView)

urlpatterns = router.urls
