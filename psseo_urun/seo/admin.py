from django.contrib import admin
from .models import SeoIcerik


@admin.register(SeoIcerik)
class SeoIcerikAdmin(admin.ModelAdmin):
    list_display  = ('urun', 'tip', 'kaynak', 'onaylandi', 'created_at')
    list_filter   = ('tip', 'kaynak', 'onaylandi')
    search_fields = ('urun__urun_kodu', 'urun__ad', 'icerik')
    readonly_fields = ('created_at',)
    list_editable   = ('onaylandi',)
