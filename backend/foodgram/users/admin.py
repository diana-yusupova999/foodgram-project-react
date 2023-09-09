from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'username')
    empty_value_display = "---"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = "---"
