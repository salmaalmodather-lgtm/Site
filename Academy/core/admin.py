from django.contrib import admin
from .models import Teacher, ContentItem


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("teacher", "week", "type", "status")
    list_filter = ("teacher", "week", "type", "status")
