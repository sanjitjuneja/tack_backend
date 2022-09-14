import datetime
from firebase_admin.messaging import (
    APNSConfig,
    APNSPayload,
    Aps,
    AndroidConfig,
    AndroidNotification
)


apns = APNSConfig(
    payload=APNSPayload(
        aps=Aps(
            sound="default",
            content_available=1
        )
    )
)

android = AndroidConfig(
    ttl=datetime.timedelta(3600),
    priority="high",
    notification=AndroidNotification(
        sound="default"
    ),
)
