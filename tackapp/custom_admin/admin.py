import logging

from django.contrib import admin


class MyAdminSite(admin.AdminSite):
    site_title = "Tack Admin"
    site_header = "Tack Admin Dashboard"
    index_title = "Tack Admin Dashboard"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        ordering = {
            # "Grafana": 0,
            # "Important": 1,
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

        apps = [
            {
                'name': 'Grafana',
                'models': [
                    {
                        'name': 'Grafana',
                        'perms': {'change': True},
                        'admin_url': 'https://grafana.backend.tackapp.net/dashboards'
                    }
                ]
            },
            {
                'name': 'Important',
                'models': [
                    {
                        'name': 'Tacks',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/tack/tack'
                    },
                    {
                        'name': 'Offers',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/tack/offer'
                    },
                    {
                        'name': 'Users',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/user/user'
                    },
                    {
                        'name': 'User Balances',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/payment/bankaccount'
                    },
                    {
                        'name': 'User Ratings',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/review/review'
                    },
                    {
                        'name': 'Groups',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/group/group'
                    },
                    {
                        'name': 'Transactions',
                        'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
                        'admin_url': '/admin/payment/transaction'
                    },
                ]
            }
        ]
        # logger = logging.getLogger('django')
        # logger.info(f"{app_list = }")

        app_list = sorted(app_list, key=lambda x: ordering[x['name']] if x['name'] in ordering else 100)
        return apps + app_list
