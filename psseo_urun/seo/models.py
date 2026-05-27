from django.db import models
from urun.models import Urun


class SeoIcerik(models.Model):
    # PrestaShop 1.7 ürün alanlarına birebir karşılık gelir
    TIP_CHOICES = [
        ('urun_adi',     'Ürün Adı Önerisi'),          # SEO uyumlu 5 alternatif ad
        ('ozet',         'Özet (Short Description)'),  # ps: short_description
        ('detay',        'Detay Açıklama (Description)'), # ps: description
        ('meta_baslik',  'Meta Başlık (Meta Title)'),  # ps: meta_title
        ('meta_aciklama','Meta Açıklama (Meta Desc)'), # ps: meta_description
        ('anahtar_kelime','Anahtar Kelimeler'),        # ps: meta_keywords
    ]
    KAYNAK_CHOICES = [
        ('ai',      'Claude AI'),
        ('chatgpt', 'ChatGPT'),
        ('sablon',  'Şablon'),
        ('manuel',  'Manuel'),
    ]

    urun       = models.ForeignKey(Urun, on_delete=models.CASCADE,
                                   related_name='seo_icerikleri', verbose_name='Ürün')
    tip        = models.CharField('İçerik Tipi', max_length=30, choices=TIP_CHOICES)
    # HTML çıktı — PrestaShop description alanı HTML kabul eder
    icerik     = models.TextField('İçerik (HTML)')
    kaynak     = models.CharField('Kaynak', max_length=10, choices=KAYNAK_CHOICES, default='ai')
    model_adi  = models.CharField('AI Model', max_length=100, blank=True)
    onaylandi  = models.BooleanField('Onaylandı', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'SEO İçerik'
        verbose_name_plural = 'SEO İçerikler'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.urun.urun_kodu} | {self.get_tip_display()} | {self.kaynak}'
