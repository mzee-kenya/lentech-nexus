from django.contrib import admin

from .models import Project, ProjectJoinRequest, ProjectMembership


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'summary', 'owner__username')
    inlines = [ProjectMembershipInline]


@admin.register(ProjectJoinRequest)
class ProjectJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('project', 'requester', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('project__title', 'requester__username')
