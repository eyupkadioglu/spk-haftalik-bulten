"""
Claude AI ile SEO içerik üretimi.
PrestaShop 1.7 uyumlu HTML çıktı döner.
"""
import anthropic
from django.conf import settings


_ORTAK_SEO_KURALLARI = """Ortak kalite kuralları:
- Çıktıyı yalnızca istenen formatta ver; açıklama, markdown veya kod bloğu ekleme.
- Ürün bilgisinde olmayan teknik iddia, stok vaadi, indirim oranı veya resmi distribütör iddiası uydurma.
- PrestaShop 1.7 uyumlu temiz HTML kullan; script, style, iframe, inline event veya dış link üretme.
- Marka, ürün adı, kategori, ürün kodu ve barkod bilgisini doğal biçimde kullan.
- Metni anahtar kelime doldurmadan yaz; satın alma niyetini, teknik netliği ve güven sinyallerini dengele.
- Türkçe yazımda sade, güven veren ve e-ticaret ürün sayfasına uygun bir ton kullan.
"""


_PROMPTS = {
    'urun_adi': """Aşağıdaki ürün için 5 farklı SEO uyumlu ürün adı önerisi hazırla.

Kurallar:
- Her öneri farklı bir hedef arama niyetini karşılasın (genel, kategori bazlı, fiyat odaklı, uzun kuyruk vb.)
- Marka adı + model + kategori kombinasyonları kullan
- Ürün adları 40-80 karakter arası olsun
- Google alışveriş ve site içi arama için optimize et
- Türkçe kelimeler kullan
- Çıktı formatı (tam olarak bu HTML yapısında):
  <p><strong>SEO Uyumlu Ürün Adı Önerileri</strong></p>
  <ol>
    <li>Öneri metni 1</li>
    <li>Öneri metni 2</li>
    ...
  </ol>
- Başka açıklama ekleme

Ürün bilgileri:
{urun_bilgi}

Çıktı (yalnızca HTML):""",

    'ozet': """Aşağıdaki ürün için PrestaShop 1.7 short_description alanına girilecek kısa bir özet yaz.

Kurallar:
- 8-10 madde içeren <ul><li> bullet listesi
- SEO dostu: birincil anahtar kelimeyi (Marka + Model) ilk maddede kullan
- Her madde 6-15 kelime, bilgilendirici ve benefit-odaklı
- Son 2 madde: teslimat ve garanti bilgisi
- Türkçe yaz
- Sadece HTML çıktı ver (sadece <ul> ve <li> etiketleri), başka açıklama ekleme

Ürün bilgileri:
{urun_bilgi}

Çıktı (yalnızca HTML):""",

    'detay': """Aşağıdaki ürün için PrestaShop 1.7 description alanına girilecek tam bir SEO açıklaması yaz.

Kurallar:
- Google SEO yapısına uy: <h1> ürün adı, <p> giriş paragrafı, <h2> bölümler, tablo, CTA
- Yapı:
  1. <h1>Marka Model</h1>
  2. <p>Giriş paragrafı — 3 cümle, birincil KW ilk 100 karakterde</p>
  3. <h2>... Teknik Özellikleri</h2> + <table><tbody> satırları
  4. <h2>... Özellikleri ve Avantajları</h2> + <ul><li> faydalar
  5. <h2>Neden ...?</h2> + <ul><li> güven sinyalleri
  6. <p>CTA — sepete ekle, fırsat, hızlı teslimat</p>
- 400-700 kelime, anahtar kelimeleri doğal dağıt
- Türkçe, ikna edici ve bilgilendirici ton
- Sadece HTML çıktı ver, ```html veya başka sarmalayıcı kullanma

Ürün bilgileri:
{urun_bilgi}

Çıktı (yalnızca HTML):""",

    'meta_baslik': """Aşağıdaki ürün için PrestaShop meta_title alanına girilecek SEO başlığı yaz.

Kurallar:
- Maksimum 70 karakter
- Marka + ürün adı + kategori içermeli
- Düz metin, HTML etiketi yok
- Türkçe

Ürün bilgileri:
{urun_bilgi}

Çıktı (yalnızca başlık metni):""",

    'meta_aciklama': """Aşağıdaki ürün için PrestaShop meta_description alanına girilecek açıklama yaz.

Kurallar:
- 150-160 karakter arası
- Anahtar kelimeler içermeli, tıklamayı teşvik etmeli
- Düz metin, HTML etiketi yok
- Türkçe

Ürün bilgileri:
{urun_bilgi}

Çıktı (yalnızca açıklama metni):""",

    'anahtar_kelime': """Aşağıdaki ürün için SEO anahtar kelimeleri listele.

Kurallar:
- Virgülle ayrılmış 8-12 anahtar kelime
- Marka adı, ürün adı, kategori, kullanım alanları dahil et
- Türkçe
- Düz metin

Ürün bilgileri:
{urun_bilgi}

Çıktı (virgülle ayrılmış kelimeler):""",
}


def _urun_bilgi_metni(urun):
    parcalar = [
        f'Marka: {urun.marka}' if urun.marka else '',
        f'Ürün Adı: {urun.ad}',
        f'Ürün Kodu: {urun.urun_kodu}',
        f'Kategori: {urun.kategori.ad}' if urun.kategori else '',
        f'Fiyat: {urun.fiyat} TL' if urun.fiyat else '',
        f'Ham Açıklama: {urun.ham_aciklama[:800]}' if urun.ham_aciklama else '',
        f'Teknik Özellikler:\n{urun.teknik_ozellik[:600]}' if urun.teknik_ozellik else '',
    ]
    return '\n'.join(p for p in parcalar if p)


def uret_ai_icerik(urun, tip):
    """
    Claude claude-sonnet-4-6 ile istenen tipte SEO içerik üretir.
    Dönen değer: (icerik_str, model_adi_str)
    """
    if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == 'your-api-key-here':
        raise ValueError('ANTHROPIC_API_KEY ayarlanmamış. .env dosyasını güncelleyin.')

    prompt_sablonu = _PROMPTS.get(tip)
    if not prompt_sablonu:
        raise ValueError(f'Bilinmeyen içerik tipi: {tip}')

    urun_bilgi = _urun_bilgi_metni(urun)
    prompt     = _ORTAK_SEO_KURALLARI + '\n\n' + prompt_sablonu.format(urun_bilgi=urun_bilgi)
    model_adi  = settings.ANTHROPIC_MODEL

    client   = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message  = client.messages.create(
        model=model_adi,
        max_tokens=2048,
        messages=[{'role': 'user', 'content': prompt}],
    )
    icerik = message.content[0].text.strip()

    # Bazen model ```html ... ``` sarmalıyor — temizle
    if icerik.startswith('```'):
        satirlar = icerik.splitlines()
        icerik   = '\n'.join(satirlar[1:-1] if satirlar[-1] == '```' else satirlar[1:]).strip()

    return icerik, model_adi
