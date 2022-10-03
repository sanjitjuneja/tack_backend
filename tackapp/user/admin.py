from datetime import timedelta

from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q, Subquery, OuterRef, Count
from django.utils import timezone

from core.choices import TackerType, TackStatus
from tack.models import Tack
from .models import *
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = user.phone_number.as_e164[1:]
        if commit:
            user.save()
        return user

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('phone_number',)


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('phone_number',)


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = (
        "id",
        "phone_number",
        "email",
        "first_name",
        "last_name",
        "allowed_to_withdraw",
        "is_staff",
        "username",
    )
    list_display_links = "phone_number",
    search_fields = ("first_name", "last_name", "phone_number",
                     "email", "username")
    search_help_text = "Search by User name, username, phone number, email"
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        (_("Personal info"), {"fields": (
            "username", "first_name", "last_name", "email",
            "profile_picture", "birthday", "tacks_amount", "tacks_rating", "active_group")}
         ),
        (
            _("Permissions"),
            {
                "fields": (
                    # "is_active",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    # "user_permissions",
                    "allowed_to_withdraw"
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', "first_name", "last_name", "email"),
        }),
    )
    ordering = ("id",)


# class TackerTypeFilter(admin.SimpleListFilter):
#     # Human-readable title which will be displayed in the
#     # right admin sidebar just above the filter options.
#     title = _('Tacker type')
#
#     # Parameter for the filter that will be used in the URL query.
#     parameter_name = 'tacker_type'
#
#     def lookups(self, request, model_admin):
#         """
#         Returns a list of tuples. The first element in each
#         tuple is the coded value for the option that will
#         appear in the URL query. The second element is the
#         human-readable name for the option that will appear
#         in the right sidebar.
#         """
#         return TackerType.choices
#
#     def queryset(self, request, queryset):
#         """
#         Returns the filtered queryset based on the value
#         provided in the query string and retrievable via
#         `self.value()`.
#         """
#         # Compare the requested value (either '80s' or '90s')
#         # to decide how to filter the queryset.
#         match self.value():
#             case TackerType.INACTIVE:
#                 return queryset.filter(
#                     Q(last_login=None) | Q(last_login__lte=timezone.now() - timedelta(days=7))
#                 )
#             case TackerType.SUPER_ACTIVE:
#                 return queryset.annotate(
#                     tacker_num=Subquery(
#                         Count(
#                             Tack.active.filter(
#                                 tacker_id=OuterRef("pk"),
#                                 status__in=(
#                                     TackStatus.WAITING_REVIEW,
#                                     TackStatus.FINISHED
#                                 )
#                             )
#                         )
#                     )
#                 )
#             case TackerType.RUNNER:
#                 return queryset.filter()
#             case TackerType.TACKER:
#                 return queryset.filter()
#             case TackerType.ACTIVE:
#                 return queryset.filter()
#             case _:
#                 return queryset
#

@admin.register(User)
class UserAdmin(AdminAdvancedFiltersMixin, CustomUserAdmin):
    list_per_page = 50
    list_display = ['id', 'phone_number', 'first_name', 'last_name', 'is_allowed_to_withdraw_money', 'tacker_type']
    list_display_links = ("phone_number",)
    list_filter = ['is_staff']
    advanced_filter_fields = (
        'tacks_rating',
        'tacks_amount',
    )
    search_fields = (
        "phone_number",
        "first_name",
        "last_name",
        "email",
    )
    search_help_text = "Search by User first_name, last_name, email, phone_number"
    ordering = ('-id',)

    @admin.display(description="Tacker type")
    def tacker_type(self, obj: User) -> TackerType:
        week_related_tacks = Tack.objects.filter(
            Q(tacker=obj) | Q(runner=obj),
            creation_time__gte=timezone.now() - timedelta(days=7),
        )
        week_num_runner_tacks = week_related_tacks.filter(
            runner=obj,
            status__in=(
                TackStatus.WAITING_REVIEW,
                TackStatus.FINISHED
            )).count()
        week_num_tacker_tacks = week_related_tacks.filter(
            tacker=obj,
        ).count()
        if not obj.last_login:
            return TackerType.INACTIVE
        if obj.last_login <= timezone.now() - timedelta(days=7):
            return TackerType.INACTIVE
        if week_num_runner_tacks >= 3 and week_num_tacker_tacks >= 1:
            return TackerType.SUPER_ACTIVE
        if week_num_runner_tacks >= 3:
            return TackerType.RUNNER
        if week_num_tacker_tacks >= 1:
            return TackerType.TACKER
        return TackerType.ACTIVE

    @admin.display(description="Withdraw", boolean=True)
    def is_allowed_to_withdraw_money(self, obj: User) -> bool:
        return obj.allowed_to_withdraw
