from django.urls import path
from .views import *


urlpatterns = [
    path(r"signup/send-code/", TwilioSendMessage.as_view(), name="signup-send-code"),
    path(
        r"signup/user-by-phone/",
        TwilioUserRegistration.as_view(),
        name="signup-registration",
    ),
    path(
        r"recovery/send-code/",
        PasswordRecoverySendMessage.as_view(),
        name="recovery-send-code",
    ),
    path(
        r"recovery/password-change/",
        PasswordRecoveryChange.as_view(),
        name="recovery-password-change",
    ),
    path(r"verify/sms-code/", VerifySMSCode.as_view(), name="verify-sms-code"),
    path(
        r"users/me/password-change/",
        PasswordChange.as_view(),
        name="accounts-password-change",
    ),
]
