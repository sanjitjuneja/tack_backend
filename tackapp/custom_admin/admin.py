from django.contrib import admin


class MyAdminSite(admin.AdminSite):
    site_title = "Tack Admin"
    site_header = "Tack administration"
    index_title = "Tack administration"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        ordering = {
            "Tack": 1,
            "Group": 2,
            "Review": 3,
            "User": 4,
            "Payment": 5,
            "Socials": 6,
            "FCM Devices": 7,
            "Periodic Tasks": 8,
            "Token Blacklist": 9,
            "ADVANCED_FILTERS": 10,
            "djstripe": 11,
            "Dwolla service": 12,
        }
        app_list = sorted(app_list, key=lambda x: ordering[x['name']] if x['name'] in ordering else 100)
        return app_list
