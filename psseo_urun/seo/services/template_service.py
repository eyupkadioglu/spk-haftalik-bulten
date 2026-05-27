"""
Sablon tabanli SEO icerik uretimi.
PrestaShop 1.7 urun alanlari icin deterministik, AI gerektirmeyen HTML ciktisi uretir.
"""
import html
import re


STOP_WORDS = {
    'icin', 'ile', 've', 'veya', 'bir', 'urun', 'urunu', 'adet', 'olan',
    'the', 'and', 'for', 'with',
}


def _temizle(metin):
    return re.sub(r'\s+', ' ', str(metin or '')).strip()


def _html(metin):
    return html.escape(_temizle(metin), quote=True)


def _dedupe(liste):
    sonuc = []
    goruldu = set()
    for deger in liste:
        temiz = _temizle(deger)
        anahtar = temiz.casefold()
        if temiz and anahtar not in goruldu:
            sonuc.append(temiz)
            goruldu.add(anahtar)
    return sonuc


def _satir_listesi(metin, limit=None):
    """Ham aciklama/teknik metni temiz, tekrar etmeyen satirlara boler."""
    parcalar = re.split(r'[\n\r;•]+|(?<=\.)\s+(?=[A-ZÇĞİÖŞÜ0-9])', metin or '')
    satirlar = []
    for s in parcalar:
        s = re.sub(r'^[\s\-*·\d\.\)]+', '', s)
        s = re.sub(r'<[^>]+>', ' ', s)
        s = _temizle(s).strip(' .')
        if len(s) >= 4:
            satirlar.append(s)
    sonuc = _dedupe(satirlar)
    return sonuc[:limit] if limit else sonuc


def _teknik_satirlar(metin, limit=15):
    """Teknik metni tabloya uygun (etiket, deger) ciftlerine donusturur."""
    sonuc = []
    for satir in _satir_listesi(metin):
        m = re.match(r'^(.{2,60}?)[\s]*[:=\-–]\s*(.{1,180})$', satir)
        if m:
            etiket = _temizle(m.group(1)).strip(':=-– ')
            deger = _temizle(m.group(2)).strip()
            if etiket and deger:
                sonuc.append((etiket, deger))
                continue
        sonuc.append(('', satir))
        if len(sonuc) >= limit:
            break
    return sonuc[:limit]


def _baslik(urun):
    marka = _temizle(urun.marka)
    ad = _temizle(urun.ad)
    if marka and not ad.casefold().startswith(marka.casefold()):
        return f'{marka} {ad}'.strip()
    return ad or marka


def _kategori_adi(urun):
    return _temizle(urun.kategori.ad) if urun.kategori else ''


def _ad_sade(urun):
    marka = _temizle(urun.marka)
    ad = _temizle(urun.ad)
    if marka:
        ad = re.sub(rf'\b{re.escape(marka)}\b', '', ad, flags=re.IGNORECASE)
    return _temizle(ad.strip(' -|')) or _baslik(urun)


def _kelime_kisalt(metin, max_karakter, ek='...'):
    metin = _temizle(metin)
    if len(metin) <= max_karakter:
        return metin
    sinir = max_karakter - len(ek)
    kirp = metin[:sinir].rsplit(' ', 1)[0].rstrip(' ,;:-')
    return (kirp or metin[:sinir].rstrip()) + ek


def _fayda_cumlesi(ozellik):
    ozellik = _temizle(ozellik).strip('.')
    if not ozellik:
        return ''
    if re.search(r'\b(garanti|kargo|fatura|orijinal|stok)\b', ozellik, re.I):
        return ozellik
    if ':' in ozellik or ' - ' in ozellik:
        return ozellik
    return f'{ozellik} ile günlük kullanımda pratik ve dengeli performans sunar'


def _liste_html(maddeler):
    satirlar = '\n'.join(f'  <li>{_html(m)}</li>' for m in _dedupe(maddeler) if _temizle(m))
    return f'<ul>\n{satirlar}\n</ul>'


def _tablo_html(satirlar):
    bolumler = ['<table>', '  <tbody>']
    for etiket, deger in satirlar:
        if not _temizle(deger):
            continue
        if etiket:
            bolumler.append(f'    <tr><td><strong>{_html(etiket)}</strong></td><td>{_html(deger)}</td></tr>')
        else:
            bolumler.append(f'    <tr><td colspan="2">{_html(deger)}</td></tr>')
    bolumler.extend(['  </tbody>', '</table>'])
    return '\n'.join(bolumler)


def _kimlik_satirlari(urun):
    kategori = _kategori_adi(urun)
    satirlar = [
        ('Marka', _temizle(urun.marka)),
        ('Kategori', kategori),
        ('Ürün Kodu', _temizle(urun.urun_kodu)),
        ('Barkod', _temizle(urun.barkod)),
        ('Fiyat', f'{urun.fiyat} TL' if urun.fiyat else ''),
    ]
    return [(etiket, deger) for etiket, deger in satirlar if deger]


def _anahtar_kelimeler(urun):
    marka = _temizle(urun.marka)
    ad = _temizle(urun.ad)
    kat = _kategori_adi(urun)
    kod = _temizle(urun.urun_kodu)
    ad_sade = _ad_sade(urun)

    kelimeler = [marka, ad, _baslik(urun), kat]
    if marka and ad_sade:
        kelimeler.append(f'{marka} {ad_sade}')
    if marka and kat:
        kelimeler.extend([f'{marka} {kat}', f'{marka} {kat} fiyat'])
    if kat:
        kelimeler.extend([f'{kat} fiyatları', f'{kat} satın al'])
    if kod:
        kelimeler.append(kod)

    for sozcuk in re.findall(r'[\wÇĞİÖŞÜçğıöşü]+', ad_sade):
        if len(sozcuk) > 3 and sozcuk.casefold() not in STOP_WORDS:
            kelimeler.append(sozcuk)

    return _dedupe(kelimeler)


def uret_ozet(urun):
    """
    PrestaShop short_description icin 8-10 maddelik, guvenli HTML bullet listesi.
    """
    marka = _temizle(urun.marka)
    kategori = _kategori_adi(urun)
    baslik = _baslik(urun)
    teknik = _teknik_satirlar(urun.teknik_ozellik, limit=6)
    ham_list = _satir_listesi(urun.ham_aciklama, limit=6)

    maddeler = []
    kimlik = f'<strong>{_html(baslik)}</strong>'
    if kategori and marka:
        maddeler.append(f'{kimlik}, {_html(kategori)} kategorisinde {_html(marka)} kalitesi sunar')
    elif kategori:
        maddeler.append(f'{kimlik}, {_html(kategori)} ihtiyacına yönelik pratik bir seçenektir')
    else:
        maddeler.append(f'{kimlik}, güvenilir kullanım ve dengeli performans için tasarlanmıştır')

    for etiket, deger in teknik:
        if etiket:
            maddeler.append(f'<strong>{_html(etiket)}:</strong> {_html(deger)}')
        else:
            maddeler.append(_html(_fayda_cumlesi(deger)))

    for satir in ham_list:
        if len(maddeler) >= 7:
            break
        fayda = _fayda_cumlesi(satir)
        if not any(satir.casefold() in m.casefold() for m in maddeler):
            maddeler.append(_html(fayda))

    if urun.urun_kodu and len(maddeler) < 8:
        maddeler.append(f'Ürün kodu: <code>{_html(urun.urun_kodu)}</code>')
    if urun.barkod and len(maddeler) < 8:
        maddeler.append(f'Barkod: <code>{_html(urun.barkod)}</code>')

    guven = [
        'Orijinal ürün, faturalı satış ve yasal garanti kapsamı',
        'Özenli paketleme ile güvenli teslimat',
        'Stok durumuna göre hızlı kargo avantajı',
    ]
    for madde in guven:
        if len(maddeler) >= 10:
            break
        maddeler.append(madde)

    satirlar = '\n'.join(f'  <li>{m}</li>' for m in maddeler[:10])
    return f'<ul>\n{satirlar}\n</ul>'


def uret_detay(urun):
    """
    PrestaShop description icin semantik HTML.
    Cikti akisi: H1, giris, urun bilgileri, teknik tablo, avantajlar,
    kullanim uygunlugu, satin alma kontrol listesi ve olculu CTA.
    """
    marka = _temizle(urun.marka)
    kategori = _kategori_adi(urun)
    baslik = _baslik(urun)
    ana_kw = baslik
    teknik = _teknik_satirlar(urun.teknik_ozellik)
    ham_list = _satir_listesi(urun.ham_aciklama, limit=10)

    bolumler = [f'<h1>{_html(baslik)}</h1>']

    konum = f'{_html(kategori)} kategorisinde' if kategori else 'ürün aramalarında'
    giris = [f'<strong>{_html(ana_kw)}</strong>, {konum} teknik bilgileri ve ürün kimliği net şekilde incelenebilen bir seçenektir.']
    if ham_list:
        giris.extend(_html(_kelime_kisalt(s, 170, ek='.')) for s in ham_list[:2])
    elif marka:
        giris.append(f'{_html(marka)} marka bilgisi, model adı ve teknik detaylarıyla doğru ürünü seçmenize yardımcı olur.')
    else:
        giris.append('Ürün kodu, kategori ve teknik açıklamalar üzerinden ihtiyacınıza uygunluğu kolayca değerlendirebilirsiniz.')
    bolumler.append(f'<p>{" ".join(giris)}</p>')

    kimlik = _kimlik_satirlari(urun)
    if kimlik:
        bolumler.append(f'<h2>{_html(baslik)} Ürün Bilgileri</h2>')
        bolumler.append(_tablo_html(kimlik))

    if teknik:
        bolumler.append(f'<h2>{_html(baslik)} Teknik Özellikleri</h2>')
        bolumler.append(_tablo_html(teknik))

    faydalar = []
    for satir in ham_list[:7]:
        faydalar.append(_fayda_cumlesi(satir))
    for etiket, deger in teknik[:6]:
        metin = f'{etiket}: {deger}' if etiket else deger
        faydalar.append(metin)
    faydalar = _dedupe(faydalar)[:6]
    if faydalar:
        bolumler.append(f'<h2>{_html(ana_kw)} Öne Çıkan Avantajları</h2>')
        bolumler.append(_liste_html(faydalar))

    kullanim = []
    if kategori:
        kullanim.append(f'{kategori} kategorisinde ürün yenileme, tamamlama veya yedekleme ihtiyacı olanlar')
    if marka:
        kullanim.append(f'{marka} marka ürün tercih eden ve model bilgisini karşılaştırmak isteyen kullanıcılar')
    kullanim.extend([
        'Ürün kodu ve teknik özellik üzerinden doğru eşleşme arayan alıcılar',
        'Faturalı alışveriş ve kayıtlı ürün bilgisiyle ilerlemek isteyen kullanıcılar',
    ])
    bolumler.append(f'<h2>{_html(baslik)} Kimler İçin Uygun?</h2>')
    bolumler.append(_liste_html(kullanim[:4]))

    kontrol = []
    if urun.urun_kodu:
        kontrol.append(f'Sipariş öncesinde ürün kodunu kontrol edin: {urun.urun_kodu}')
    if urun.barkod:
        kontrol.append(f'Barkod bilgisini mevcut ürününüzle karşılaştırın: {urun.barkod}')
    if kategori:
        kontrol.append(f'Kategori uyumunu kontrol edin: {kategori}')
    kontrol.extend([
        'Teknik özelliklerde yer alan ölçü, model, renk veya kapasite bilgisini ihtiyacınızla eşleştirin',
        'Kargo, iade ve garanti koşullarını sipariş ekranında gözden geçirin',
    ])
    bolumler.append(f'<h2>{_html(baslik)} Satın Almadan Önce</h2>')
    bolumler.append(_liste_html(kontrol[:5]))

    neden = []
    if marka:
        neden.append(f'{marka} marka ve model bilgisiyle aradığınız ürünü daha kolay doğrulayabilirsiniz')
    if teknik:
        neden.append('Teknik özelliklerin tablo halinde sunulması karşılaştırmayı kolaylaştırır')
    neden.extend([
        'Ürün adı, kategori ve kimlik bilgileri SEO uyumlu ve okunabilir yapıdadır',
        'Açıklama metni PrestaShop ürün sayfasında doğrudan kullanılabilecek temiz HTML ile hazırlanır',
    ])
    bolumler.append(f'<h2>Neden {_html(baslik)}?</h2>')
    bolumler.append(_liste_html(neden[:5]))

    bolumler.append(
        f'<p><strong>{_html(baslik)}</strong> ürününü sepetinize eklemeden önce '
        'ürün kodu, kategori ve teknik özellik bilgilerini kontrol ederek siparişinizi güvenle tamamlayabilirsiniz.</p>'
    )
    return '\n'.join(bolumler)


def uret_meta_baslik(urun):
    marka = _temizle(urun.marka)
    kat = _kategori_adi(urun)
    baslik = _baslik(urun)
    ad_sade = _ad_sade(urun)

    secenekler = []
    if marka and ad_sade and kat:
        secenekler.append(f'{marka} {ad_sade} {kat} Fiyatı')
    if marka and ad_sade:
        secenekler.append(f'{marka} {ad_sade} Fiyatı ve Özellikleri')
        secenekler.append(f'{marka} {ad_sade} Satın Al')
    if kat:
        secenekler.append(f'{baslik} | {kat}')
    secenekler.extend([f'{baslik} Fiyatı', baslik])

    for secenek in _dedupe(secenekler):
        if len(secenek) <= 70:
            return secenek
    return _kelime_kisalt(baslik, 70, ek='')


def uret_meta_aciklama(urun):
    kat = _kategori_adi(urun)
    baslik = _baslik(urun)
    ham_list = _satir_listesi(urun.ham_aciklama, limit=1)

    if ham_list:
        temel = f'{baslik}: {_kelime_kisalt(ham_list[0], 72, ek="")}.'
    elif kat:
        temel = f'{baslik}, {kat} kategorisinde orijinal ve faturalı ürün seçeneği.'
    else:
        temel = f'{baslik} için orijinal ürün, faturalı satış ve güvenli alışveriş avantajı.'

    aciklama = f'{temel} Hızlı kargo, yasal garanti ve güvenli ödeme ile hemen satın alın.'
    return _kelime_kisalt(aciklama, 160)


def uret_urun_adi(urun):
    marka = _temizle(urun.marka)
    kat = _kategori_adi(urun)
    kod = _temizle(urun.urun_kodu)
    ad_sade = _ad_sade(urun)
    baslik = _baslik(urun)

    oneriler = [
        f'{marka} {ad_sade} {kat}'.strip(),
        f'{baslik} Fiyatı ve Özellikleri',
        f'{baslik} Satın Al',
    ]
    if kat:
        oneriler.append(f'{kat} için {baslik}')
    if kod:
        oneriler.append(f'{baslik} {kod} Orijinal Ürün')
    if marka and kat:
        oneriler.append(f'{marka} {kat} Ürünü - {ad_sade}')
    oneriler.append(f'{baslik} Orijinal ve Faturalı')

    temiz_oneriler = [_kelime_kisalt(o, 80, ek='') for o in _dedupe(oneriler) if len(o) >= 12]
    while len(temiz_oneriler) < 5:
        temiz_oneriler.append(f'{baslik} - SEO Ürün Adı {len(temiz_oneriler) + 1}')

    satirlar = '\n'.join(f'  <li>{_html(o)}</li>' for o in temiz_oneriler[:5])
    return (
        '<p><strong>SEO Uyumlu Ürün Adı Önerileri</strong></p>\n'
        f'<ol>\n{satirlar}\n</ol>'
    )


def uret_anahtar_kelime(urun):
    kelimeler = _anahtar_kelimeler(urun)
    ticari = []
    baslik = _baslik(urun)
    kat = _kategori_adi(urun)
    if baslik:
        ticari.extend([f'{baslik} fiyat', f'{baslik} satın al'])
    if kat:
        ticari.append(f'orijinal {kat}')
    return ', '.join(_dedupe(kelimeler + ticari)[:14])


TIP_FONK = {
    'urun_adi': uret_urun_adi,
    'ozet': uret_ozet,
    'detay': uret_detay,
    'meta_baslik': uret_meta_baslik,
    'meta_aciklama': uret_meta_aciklama,
    'anahtar_kelime': uret_anahtar_kelime,
}


def uret_sablon_icerik(urun, tip):
    fonk = TIP_FONK.get(tip)
    if not fonk:
        raise ValueError(f'Bilinmeyen içerik tipi: {tip}')
    return fonk(urun)
