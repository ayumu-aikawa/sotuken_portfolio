from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import User
# from django.utils.translation import gettext, gettext_lazy as _

# admin.site.register(User)

# class AdminUserAdmin(UserAdmin):

#     fieldsets = (
#         (None, {'fields': ('username', 'password', 'email')}),
#         (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
#                                        'groups', 'user_permissions')}),
#         (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
#     )
#     list_display = ('username', 'email', 'is_staff')
#     search_fields = ('username', 'email')
#     filter_horizontal = ('groups', 'user_permissions','departments')