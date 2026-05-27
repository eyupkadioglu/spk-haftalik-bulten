from django.contrib import admin
from .models import Kategori, Urun


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display  = ('ad', 'slug', 'ust')
    prepopulated_fields = {'slug': ('ad',)}
    search_fields = ('ad',)


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display   = ('urun_kodu', 'marka', 'ad', 'kategori', 'seo_durumu', 'created_at')
    list_filter    = ('marka', 'kategori')
    search_fields  = ('urun_kodu', 'marka', 'ad', 'barkod')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Kimlik', {'fields': ('urun_kodu', 'marka', 'ad', 'kategori', 'barkod', 'fiyat')}),
        ('Kaynak', {'fields': ('kaynak_url', 'tedarikci_kodu')}),
        ('Ham İçerik', {'fields': ('ham_aciklama', 'teknik_ozellik'), 'classes': ('collapse',)}),
        ('Meta', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
