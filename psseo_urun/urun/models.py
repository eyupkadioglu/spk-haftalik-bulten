from django.db import models
from django.utils.text import slugify


class Kategori(models.Model):
    ad   = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    ust  = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='alt_kategoriler')

    class Meta:
        verbose_name        = 'Kategori'
        verbose_name_plural = 'Kategoriler'
        ordering            = ['ad']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ad, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ad


class Urun(models.Model):
    urun_kodu      = models.CharField('Ürün Kodu', max_length=200, unique=True)
    marka          = models.CharField('Marka', max_length=200, blank=True)
    ad             = models.CharField('Ürün Adı', max_length=500)
    kategori       = models.ForeignKey(Kategori, null=True, blank=True,
                                       on_delete=models.SET_NULL, verbose_name='Kategori')
    tedarikci_kodu = models.CharField('Tedarikçi Kodu', max_length=200, blank=True)
    barkod         = models.CharField('Barkod (EAN)', max_length=50, blank=True)
    kaynak_url     = models.URLField('Kaynak URL', max_length=2000, blank=True,
                                     help_text='Ürünün bulunduğu web sayfası — içerik buradan çekilir')
    fiyat          = models.DecimalField('Fiyat', max_digits=12, decimal_places=2,
                                         null=True, blank=True)
    ham_aciklama   = models.TextField('Ham Açıklama', blank=True,
                                      help_text='Tedarikçiden gelen, düzenlenmemiş açıklama')
    teknik_ozellik = models.TextField('Teknik Özellikler', blank=True,
                                      help_text='Madde madde veya serbest metin')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Ürün'
        verbose_name_plural = 'Ürünler'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.urun_kodu} — {self.ad}'

    def seo_durumu(self):
        icerikleri = self.seo_icerikleri.all()
        if not icerikleri.exists():
            return 'uretilmedi'
        if icerikleri.filter(onaylandi=True).exists():
            return 'onaylandi'
        return 'uretildi'
