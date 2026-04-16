from django.contrib import admin
from .models import Sponsor


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'order', 'active']
    list_filter = ['active']
    search_fields = ['name']
    ordering = ['order', 'name']
    list_editable = ['order', 'active']
