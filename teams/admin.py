from django.contrib import admin
from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'has_regulation')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    prepopulated_fields = {'slug': ('name',)}

    def has_regulation(self, obj):
        return bool(obj.regulation)
    has_regulation.boolean = True
    has_regulation.short_description = 'Regolamento'
