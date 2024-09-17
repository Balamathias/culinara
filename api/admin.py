from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Post, User, Tag

class AppUserAdmin(UserAdmin):
    # list_display = ('email', 'username', 'first_name', 'last_name', 'phone', 'is_staff', 'is_superuser', 'is_active')
    # search_field = ('email', 'username', 'first_name', 'last_name', 'phone')
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    ordering = ('email',)


admin.site.register(User, AppUserAdmin)
admin.site.register(Post)
admin.site.register(Tag)
admin.site.site_header = 'Culinara Administration'
