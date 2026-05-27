from django.test import TestCase

from urun.models import Kategori, Urun
from seo.services.template_service import (
    TIP_FONK,
    uret_detay,
    uret_meta_aciklama,
    uret_meta_baslik,
    uret_ozet,
    uret_sablon_icerik,
)


class SeoSablonServiceTests(TestCase):
    def setUp(self):
        kategori = Kategori.objects.create(ad='Kartuş ve Toner')
        self.urun = Urun.objects.create(
            urun_kodu='HP-305XL',
            marka='HP',
            ad='305XL Siyah Mürekkep Kartuşu <script>alert(1)</script>',
            kategori=kategori,
            barkod='1234567890123',
            fiyat='399.90',
            ham_aciklama=(
                'Yüksek sayfa verimi sunar. Net siyah baskılar üretir. '
                'Ev ve ofis kullanımı için uygundur.'
            ),
            teknik_ozellik='Renk: Siyah\nUyumlu Model: DeskJet 2710\nKapasite: 240 sayfa',
        )

    def test_tum_sablon_tipleri_icerik_uretir(self):
        for tip in TIP_FONK:
            with self.subTest(tip=tip):
                self.assertTrue(uret_sablon_icerik(self.urun, tip).strip())

    def test_ozet_guvenli_html_ve_liste_uretir(self):
        html = uret_ozet(self.urun)

        self.assertTrue(html.startswith('<ul>'))
        self.assertIn('<li>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)

    def test_detay_semantik_bolumler_ve_teknik_tablo_uretir(self):
        html = uret_detay(self.urun)

        self.assertIn('<h1>', html)
        self.assertIn('<h2>', html)
        self.assertIn('<table>', html)
        self.assertIn('Ürün Bilgileri', html)
        self.assertIn('Kimler İçin Uygun?', html)
        self.assertIn('Satın Almadan Önce', html)
        self.assertIn('<strong>Renk</strong>', html)
        self.assertIn('Siyah', html)
        self.assertNotIn('<script>', html)

    def test_meta_alanlari_prestashop_sinirlarina_uyar(self):
        baslik = uret_meta_baslik(self.urun)
        aciklama = uret_meta_aciklama(self.urun)

        self.assertLessEqual(len(baslik), 70)
        self.assertLessEqual(len(aciklama), 160)
        self.assertFalse(baslik.endswith(' '))
        self.assertFalse(aciklama.endswith(' '))
