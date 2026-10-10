from django.contrib import admin

from .models import Idea, IdeaInterest


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'summary', 'author__username')


@admin.register(IdeaInterest)
class IdeaInterestAdmin(admin.ModelAdmin):
    list_display = ('idea', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('idea__title', 'user__username')