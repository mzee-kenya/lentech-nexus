from django.contrib import admin

from .models import Developer


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'user', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('name', 'role', 'skills', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
