from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'recipe_count')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('email', 'first_name')

    def recipe_count(self, obj):
        return obj.recipes.count()
    recipe_count.short_description = 'Количество рецептов'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')