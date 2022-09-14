from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"tacks", TackViewset)
router.register(r"offers", OfferViewset)

urlpatterns = router.urls
