# Script to add labels to sub-headings in "## Dosya Bazlı Hiyerarşi" section
# Uses U+2019 (right single quote ') for Turkish apostrophes in the file

RSQUOTE = '’'  # Right single quote U+2019 used as apostrophe in the file


def classify_line(text, section_header=''):
    """Classify a sub-heading line and return the appropriate label.
    section_header: the current section name (YENİ FAALİYET etc.)
    """
    t = text

    # --- Emeklilik Yatırım Fonu ---
    emeklilik_sirketler = [
        'Bereket Emeklilik',
        'Allianz Yaşam',
        'Anadolu Hayat Emeklilik',
        'Agesa Hayat ve Emeklilik',
        'Agesa Hayat',
        'Katılım Emeklilik',
        'Garanti Emeklilik',
        'Metlife Emeklilik',
        'BNP Paribas Cardif Emeklilik',
        'HDI Fiba Emeklilik',
        'Türkiye Hayat ve Emeklilik',
    ]
    has_emeklilik_sirket = any(s in t for s in emeklilik_sirketler)
    has_emeklilik_fonu = ('Emeklilik Yatırım Fonu' in t or
                          ('Hisse Senedi Emeklilik' in t and 'YENİ FAALİYET' in section_header) or
                          ('Emeklilik' in t and 'Fon Sepeti Emeklilik' in t))

    if has_emeklilik_sirket:
        if has_emeklilik_fonu:
            return '[Emeklilik Yatırım Fonu]'
        if t.endswith('Emeklilik') and 'YENİ FAALİYET' in section_header:
            return '[Emeklilik Yatırım Fonu]'
        if 'Emeklilik' in t and 'YENİ FAALİYET' in section_header and 'Emeklilik Yatırım Fonu Payları' not in t:
            if 'kuruluşuna izin' in t or t[-20:].count('Emeklilik') > 0:
                return '[Emeklilik Yatırım Fonu]'

    # --- Gayrimenkul Semsiye Fonu ---
    if 'Gayrimenkul Şemsiye Fonu' in t:
        return '[Gayrimenkul Şemsiye Fonu]'

    # --- Girisim Sermayesi Semsiye Fonu ---
    if 'Girişim Sermayesi Şemsiye Fonu' in t:
        return '[Girişim Sermayesi Şemsiye Fonu]'
    # More specific: Alkima truncated pattern
    if 'Alkima Girişim Sermayesi' in t and 'YENİ FAALİYET' in section_header:
        if t.rstrip().endswith('Sermayesi') or 'Şemsiye Fonu' in t:
            return '[Girişim Sermayesi Şemsiye Fonu]'

    # --- Hisse Senedi Semsiye Fonu ---
    if 'Hisse Senedi Şemsiye Fonu' in t:
        return '[Hisse Senedi Şemsiye Fonu]'

    # --- Borsa Yatirim Fonu ---
    if 'Borsa Yatırım Fonu' in t:
        if 'ünvanlarına yer verilen borsa yatırım fonları' in t:
            return '[Toplu Fon Kuruluşu]'
        return '[Borsa Yatırım Fonu]'

    # --- Yatirim Ortakligi Kurulusu ---
    if ('kayıtlı sermaye tavanı' in t or 'kayıtlı sermaye tavan' in t) and 'başlangıç sermayeli' in t:
        if 'Girişim Sermayesi Yatırım Ortaklığı' in t:
            return '[Yatırım Ortaklığı Kuruluşu]'
        if 'Girişim Sermayesi' in t and 'YENİ FAALİYET' in section_header:
            return '[Yatırım Ortaklığı Kuruluşu]'
        if 'Girişim Sermayesi' in t:
            return '[Yatırım Ortaklığı Kuruluşu]'

    # --- Toplu Fon Kurulusu ---
    if 'Aşağıda ünvanlarına yer verilen' in t and 'kuruluşlarına izin' in t:
        return '[Toplu Fon Kuruluşu]'
    if 'Aşağıda ünvanlarına yer verilen' in t and 'kuruluşuna izin verilmesi talepleri olumlu' in t:
        return '[Toplu Fon Kuruluşu]'
    if 'şemsiye fonların kuruluşuna izin verilmesi talepleri olumlu' in t:
        return '[Toplu Fon Kuruluşu]'
    if 'Aşağıda ünvanlarına yer verilen' in t and 'kuruluşuna izin' in t:
        if 'katılma paylarının ihracına' in t or 'halka arzına' in t:
            return '[Toplu Fon Kuruluşu]'
    if 'ünvanlarına yer verilen girişim sermayesi yatırım fonlarının kuruluşuna' in t:
        return '[Toplu Fon Kuruluşu]'

    # --- Gayrimenkul Yatirim Fonu (individual) ---
    if 'Gayrimenkul Yatırım Fonu' in t:
        return '[Gayrimenkul Yatırım Fonu]'
    # Truncated: Arz Gayrimenkul pattern (company name appears twice)
    arz_gyf_pattern = 'Arz Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi'
    if arz_gyf_pattern in t and 'YENİ FAALİYET' in section_header:
        if t.count('Arz Gayrimenkul') >= 2:
            return '[Gayrimenkul Yatırım Fonu]'
    # Kalkınma GSYF pattern
    if 'Kalkınma Girişim Sermayesi Portföy Yönetimi' in t and 'YENİ FAALİYET' in section_header:
        return '[Girişim Sermayesi Yatırım Fonu]'

    # --- Girisim Sermayesi Yatirim Fonu (individual) ---
    if 'Girişim Sermayesi Yatırım Fonu' in t:
        return '[Girişim Sermayesi Yatırım Fonu]'

    # --- Ortaklik Yapisi Degisikligi ---
    if 'ortaklık yapısındaki değişikliklere izin' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    if 'ortaklık yapısındaki değişikliklere onay' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    if 'ortaklık yapısındaki değişikliğe izin' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    if 'ortaklık yapısının' in t and 'sayılı' in t and 'Yatırım Kuruluşlarının Kuruluş' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    if 'ortaklık yapısı,' in t and 'Tebliği' in t:
        return '[Ortaklık Yapısı Değişikliği]'

    # --- Kurum Sermaye Artirimi ---
    if f'TL{RSQUOTE}den' in t and f'TL{RSQUOTE}ye artırılmasına' in t:
        return '[Kurum Sermaye Artırımı]'
    if "TL'den" in t and "TL'ye artırılmasına" in t:
        return '[Kurum Sermaye Artırımı]'
    if 'kayıtlı sermaye tavanı' in t and 'başlangıç sermayeli' not in t and \
       'Girişim Sermayesi Yatırım Ortaklığı' not in t and 'Girişim Sermayesi' not in t:
        if 'ORTAKLIK YAPISI' in section_header or 'SERMAYE PİYASASI' in section_header:
            return '[Kurum Sermaye Artırımı]'

    # --- Toplu Izahname Onayi ---
    if 'ünvanlarına yer verilen fonların katılma paylarının ihracına ilişkin izahname' in t:
        return '[Toplu İzahname Onayı]'
    if 'ünvanına yer verilen fonlar' in t and 'katılma paylarının ihracına' in t and 'izahname' in t:
        return '[Toplu İzahname Onayı]'
    if 'ünvanına yer verilen fonun katılma paylarının ihracına' in t and 'izahname' in t:
        return '[Toplu İzahname Onayı]'
    if 'ünvanlarına yer verilen' in t and 'katılma paylarının ihracına ilişkin' in t:
        return '[Toplu İzahname Onayı]'
    # Typo case: missing "verilen"
    if 'ünvanlarına yer fonların katılma paylarının ihracına' in t and 'izahname' in t:
        return '[Toplu İzahname Onayı]'

    # --- Toplu Fon Donusumu ---
    if 'ünvanlarına yer verilen fonların dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanına yer verilen fonun dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanına yer verilen fonların dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanına yer verilen emeklilik yatırım fonunun dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanlarına yer verilen emeklilik yatırım fonlarının dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanlarına yer verilen' in t and 'dönüşüm' in t and 'izahname tadil' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanlarına yer verilen' in t and 'dönüşümüne izin' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanlarına yer verilen' in t and 'dönüşümlerine izin' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanına yer verilen' in t and 'dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'
    if 'ünvanlarına yer verilen' in t and 'dönüşüm' in t:
        return '[Toplu Fon Dönüşümü]'

    # --- Toplu Fon Tasfiyesi ---
    if 'ünvanlarına yer verilen fonların tasfiye' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'ünvanına yer verilen fonların tasfiye' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'ünvanına yer verilen fonun' in t and 'tasfiye' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'ünvanına yer verilen' in t and 'tasfiye' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'ünvanlarına yer verilen şemsiye fon ve fonların tasfiye' in t:
        return '[Toplu Fon Tasfiyesi]'

    # --- Toplu Fon Birlesme ---
    if 'ünvanlarına yer verilen fonların birleşme' in t:
        return '[Toplu Fon Birleşmesi]'
    if 'emeklilik yatırım fonlarının birleşme' in t:
        return '[Toplu Fon Birleşmesi]'
    if 'ünvanlarına yer verilen' in t and 'birleşme' in t:
        return '[Toplu Fon Birleşmesi]'
    if 'ünvanına yer verilen fonların birleşme' in t:
        return '[Toplu Fon Birleşmesi]'

    # --- Esas Sozlesme Degisikligi ---
    if 'esas sözleşmesinin' in t and 'maddes' in t:
        return '[Esas Sözleşme Değişikliği]'

    # --- Istirak Islemi ---
    if f'%100{RSQUOTE}üne sahip' in t and 'halka açık' in t:
        return '[İştirak İşlemi]'
    if "%100'üne sahip" in t and 'halka açık' in t:
        return '[İştirak İşlemi]'
    if '%100' in t and 'halka açık' in t and 'sahip' in t:
        return '[İştirak İşlemi]'

    # --- GYO Donusumu ---
    if 'ünvanlı bir gayrimenkul yatırım ortaklığı' in t:
        return '[GYO Dönüşümü]'
    if 'ünvanlı bir' in t and ('Gayrimenkul Yatırım' in t or 'GYO' in t or 'gayrimenkul' in t.lower()):
        if 'Portföy' not in t:
            return '[GYO Dönüşümü]'

    # --- Varlik Kiralama Sirketi ---
    if 'Kira Sertifikaları Tebliği' in t and 'Varlık Kiralama' in t:
        return '[Varlık Kiralama Şirketi]'
    if 'III-61.1 sayılı Kira Sertifikaları Tebliği' in t:
        return '[Varlık Kiralama Şirketi]'
    if 'Kira Sertifikaları Tebliği' in t and ('hükümleri' in t or 'çerçevesinde' in t):
        return '[Varlık Kiralama Şirketi]'

    # --- Esas Sozlesme Degisikligi (additional patterns for truncated lines) ---
    # Lines with 'esas sözleşmesinin' + madde number (even without 'maddes')
    if 'esas sözleşmesinin' in t:
        import re as _re
        # Check for article/paragraph references
        if _re.search(r'\d+\s*(nci|inci|üncü|ncı|ıncı|uncu|üncü)\s*madde', t):
            return '[Esas Sözleşme Değişikliği]'
        if _re.search(r'\d+[,. ]+\d+.*madde', t):
            return '[Esas Sözleşme Değişikliği]'
        if 'başlıklı' in t or 'başlıkl' in t:
            return '[Esas Sözleşme Değişikliği]'
        # Article numbers like "4, 6, 9"
        if _re.search(r'[0-9][\d,\s]+ve\s+\d+', t):
            return '[Esas Sözleşme Değişikliği]'
        # Truncated: title begins with left double quote (U+201C)
        if '“' in t or '"' in t:
            return '[Esas Sözleşme Değişikliği]'
        # Any esas sozlesmesinin mention → likely ESZ
        return '[Esas Sözleşme Değişikliği]'

    # --- Kurum Sermaye Artirimi (general patterns) ---
    # "çıkarılmış" at end of truncated line (would be "çıkarılmış sermayesinin")
    if t.rstrip().endswith('çıkarılmış') and 'AŞ' in t:
        return '[Kurum Sermaye Artırımı]'
    # kayıtlı sermaye tavanı içerisinde ... TL olan
    if 'kayıtlı sermaye tavanı içerisinde' in t or 'kayıtlı sermaye tavanı içinde' in t:
        return '[Kurum Sermaye Artırımı]'
    # kayıtlı sermaye sistemi içerisinde (variant)
    if 'kayıtlı sermaye sistemi içerisinde' in t:
        return '[Kurum Sermaye Artırımı]'
    if 'kayıtlı sermaye tavanı ile kayıtlı sermaye sistemine' in t:
        return '[Kurum Sermaye Artırımı]'
    # kayıtlı sermaye tavanı (any mention without fund context - but GSYO is OK here)
    if 'kayıtlı sermaye tavan' in t and 'Yatırım Fonu' not in t:
        return '[Kurum Sermaye Artırımı]'
    # ödenmiş sermayesinin ... TL'ye / artırılmasına
    if 'ödenmiş sermayesinin' in t:
        return '[Kurum Sermaye Artırımı]'
    # çıkarılmış sermayesinin ... TL (Girişim Sermayesi Yatırım Ortaklığı = GSYO = company, NOT a fund)
    if 'çıkarılmış sermayesinin' in t:
        return '[Kurum Sermaye Artırımı]'
    # başlangıç sermayesinin (for GSYO not GSYF)
    if 'başlangıç sermayesinin' in t and 'Yatırım Ortaklığı' in t:
        return '[Kurum Sermaye Artırımı]'
    # kayıtlı sermaye sistemine geçiş
    if 'kayıtlı sermaye sistemine geçiş' in t:
        return '[Kurum Sermaye Artırımı]'
    # sermaye artırımı (explicit)
    if 'sermaye artırımı' in t and 'Yatırım Fonu' not in t:
        return '[Kurum Sermaye Artırımı]'
    # kayıtlı sermaye sisteminden çıkış (reverse, still same category)
    if 'kayıtlı sermaye sisteminden çıkış' in t:
        return '[Kurum Sermaye Artırımı]'

    # --- Ortaklik Yapisi Degisikligi (additional patterns) ---
    # Share transfers: person/company has shares in another company
    if 'sahip olduğu' in t and ('nominal' in t or 'payların' in t or 'paylarının' in t):
        if 'Girişim Sermayesi Yatırım Fonu' not in t and 'Emeklilik Yatırım Fonu' not in t:
            return '[Ortaklık Yapısı Değişikliği]'
    # sahip olduğu + TL amount (truncated, no nominal/payları at end)
    if 'sahip olduğu' in t and 'sermayesinde' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # tüzel kişi ortağı
    if 'tüzel kişi ortağı' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # ortakları ... (multiple person names as shareholders)
    if 'ortakları' in t and t.count('AŞ') == 1:
        return '[Ortaklık Yapısı Değişikliği]'
    # "ortağı ... sahip olduğu" (singular)
    if 'ortağı' in t and 'sahip olduğu' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "ortağı ... sahip" (without olduğu, truncated)
    if 'ortağı' in t and 'sermayesinde sahip' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # Person's name (uppercase person name) + "sermayesinde sahip"
    if 'sermayesinde sahip' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "A grubu imtiyazlı paylarının tamamına sahip olan"
    if 'imtiyazlı paylarının tamamına sahip' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # Shareholder paying / devir
    if 'payların tamamının' in t and 'devrine izin' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "sermayesinde ... Minereks ... AŞ" (multiple shareholders listed)
    if 'sermayesinde' in t and t.count('AŞ') >= 3 and 'Fon' not in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "geri alınan paylardan/paylarından" (share buyback)
    if 'geri alınan paylar' in t or 'Geri Alınan Paylar Tebliği' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "sahibi olduğu" + "adet" (truncated share transfer)
    if 'sahibi olduğu' in t and 'adet' in t:
        return '[Ortaklık Yapısı Değişikliği]'
    # "ortağı ... sermayesinde" (truncated share transfer, ortağı without sahip olduğu)
    if 'ortağı' in t and 'sermayesinde' in t:
        return '[Ortaklık Yapısı Değişikliği]'

    # --- Toplu Fon Tasfiyesi (individual fund liquidation) ---
    # Single fund: "X Portföy Yönetimi AŞ'nin ... Fon'un tasfiye edilmesine"
    if 'tasfiye edilmesine izin' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'tasfiye edilmesine' in t and 'talebi olumlu' in t:
        return '[Toplu Fon Tasfiyesi]'
    if 'tasfiye edilmesine' in t:
        return '[Toplu Fon Tasfiyesi]'
    # "kurucusu olduğu ... Fon ve X" (multiple funds being dissolved)
    if 'kurucusu olduğu' in t and 'Fon' in t and 'tasfiye' not in t:
        # Two funds (e.g. Garanti Portföy ... Fon ve Garanti ... Fon)
        if t.count('Fon') >= 2:
            return '[Toplu Fon Tasfiyesi]'
    # "kurucusu olduğu ... Fon'un" (individual fund tasfiye - truncated, RSQUOTE apostrophe)
    FONUN = f"Fon{RSQUOTE}un"
    if 'kurucusu olduğu' in t and (FONUN in t or "Fon'un" in t):
        return '[Toplu Fon Tasfiyesi]'
    # "kurucusu olduğu ... Fon (Hisse Senedi" - truncated
    if 'kurucusu olduğu' in t and 'Fon' in t and 'Hisse Senedi' in t:
        return '[Toplu Fon Tasfiyesi]'
    # "kurucusu olduğu ... Yatırım" at end (truncated Gayrimenkul Yatırım Fonu)
    if 'kurucusu olduğu' in t and t.rstrip().endswith('Yatırım'):
        return '[Toplu Fon Tasfiyesi]'
    # Direct fund tasfiyesi: "X Portföy ... Fon'un (Hisse Senedi Yoğun Fon)" - truncated before "tasfiye"
    FONUN2 = f"Fon{RSQUOTE}un"
    if 'Portföy' in t and (FONUN2 in t or "Fon'un" in t) and 'Yoğun Fon' in t:
        return '[Toplu Fon Tasfiyesi]'

    # --- İstirak İslemi - additional patterns ---
    # "sermayesinin ve oy hakkı veren paylarının tamamına sahip olduğu, halka açık olmayan"
    if 'oy hakkı veren paylarının tamamına sahip' in t and 'halka açık' in t:
        return '[İştirak İşlemi]'
    # "sermayesinin ve oy hakkı veren paylarının %100'üne sahip olduğu bağlı"
    if 'oy hakkı veren paylarının' in t and '%100' in t:
        return '[İştirak İşlemi]'
    # Truncated: "paylarının %100'üne" at end
    if 'paylarının %100' in t:
        return '[İştirak İşlemi]'
    # "birleşmeye esas ... finansal tabloları itibarıyla sermayesinin ve oy hakkı"
    if 'birleşmeye esas' in t and 'oy hakkı' in t:
        return '[İştirak İşlemi]'
    # "birleşmeye esas ... tarihli" (truncated)
    if 'birleşmeye esas' in t and 'tarihli' in t:
        return '[İştirak İşlemi]'
    # "yönetim kontrolünü elde"
    if 'yönetim kontrolünü elde' in t:
        return '[İştirak İşlemi]'
    # "sahibi olduğu %xx oranındaki ... paylarının tamamının"
    if 'sahibi olduğu' in t and 'oranındaki' in t:
        return '[İştirak İşlemi]'
    # "tarafından, X AŞ'nin ... tarihli finansal tablolar" (acquisition subject to SPK review)
    import re as _re2
    if 'tarafından,' in t and _re2.search(r'\d{2}\.\d{2}\.\d{4} tarihli finansal', t):
        return '[İştirak İşlemi]'
    # "tarafından, X AŞ'nin" (truncated - no date visible, RSQUOTE)
    if 'tarafından,' in t and (f'AŞ{RSQUOTE}nin' in t or "AŞ'nin" in t):
        return '[İştirak İşlemi]'
    # "Birleşme ve Bölünme Tebliği" - merger
    if 'Birleşme ve Bölünme Tebliği' in t:
        return '[İştirak İşlemi]'
    # Truncated: "II-23.2 sayılı Birleşme ve" (before "Bölünme Tebliği")
    if 'II-23.2 sayılı Birleşme' in t:
        return '[İştirak İşlemi]'
    # X AŞ ... tarihli finansal tablolar (acquisition review, no tarafından)
    if "tarihli finansal tablolar" in t:
        return ‘[İştirak İşlemi]’
    # Partial stake acquisition: "sermayesinin %x oranına, oy haklarının"
    if 'sermayesinin %' in t and 'oy haklarının' in t:
        return '[İştirak İşlemi]'

    # --- Standart headings ---
    standart_keywords = [
        'İdari Para Cezaları',
        'fıkrası',  # Article sub-section references (L296, L297, L1536)
        'Suç Duyuruları',
        'Diğer Yaptırım',
        'İşlem Yasakları',
        'Lisans ve Yetki Belgesi İptalleri',
        'Fon Kuruluşu',
        'Yetki Belgesi Alınması',
        'Yatırım Kuruluşlarının Yetkilendirilmesi',
        'Bağımsız Denetim Kuruluşlarının Yetkilendirilmesi',
        'Derecelendirme Kuruluşlarının Yetkilendirilmesi',
        'Değerleme Şirketlerinin Yetkilendirilmesi',
        'Makine ve Ekipmanları Değerlemeye',
        'Gayrimenkul Dışındaki Varlıkları Değerlemeye',
        'Gayrimenkul Dışı Varlıkları Değerlemeye',
        'Diğer faaliyet izinleri',
        'Diğer Faaliyet İzinleri',
        'Varlık Kiralama Şirketi Kuruluşu',
        'İlk Halka Arzlar',
        'Halka Açık Ortaklıkların Pay İhraçları',
        'Diğer Ortaklıkların Pay İhraçları',
        'Borçlanma Araçları',
        'Emeklilik Yatırım Fonu Payları',
        'Diğer Sermaye Piyasası Araçları',
        'Devredilen Fonlar',
        'Portföy Yönetim Şirketi Kuruluşu',
        'Aracı Kurum Kuruluşu',
        'Portföy Yönetim Şirketlerinin Sermaye Artırımları',
        'Yatırım Kuruluşlarının Sermaye Artırımları',
        'Yatırım Kuruluşlarının Merkez Dışı Örgüt',
        'Kendi İsteğiyle',
        'Yetkilendirme Değişikliği',
        'Diğer Başvurular',
        'İlke Kararları',
        'Duyurular',
        'Kurul Karar Organı',
        'i-SPK',
        'Grup Şirketler',
        'Faaliyetleri Geçici Durdurma',
        'Yetkilendirilen Platformlar Listesinden',
        'Kripto Varlık Hizmet Sağlayıcı',
        'Portföy Yönetim Şirketi',
        'portföy yönetim şirketi',  # lowercase variant
        'Değerleme Şirketi',
        'Değerleme Kuruluşu',
        'Yetkili Kuruluşlar',  # Değerlemeye Yetkili Kuruluşlar variants
        'faaliyet izni ile portföy',  # Yetki belgesi granting
        'kurumsal yönetim ilkelerinden',  # Duyuru / İlke kararı followup
        'Tebliğ kapsamında',  # Duyuru continuation
    ]
    for kw in standart_keywords:
        if kw in t:
            return '[Standart]'

    # Additional İzahname checks
    if 'ilk halka arzına ilişkin izahname' in t:
        return '[Standart]'
    if 'Şemsiye Fon' in t and 'bağlı olarak ihraç' in t:
        return '[Toplu İzahname Onayı]'

    return '[Diğer]'


import re

# Read the file
with open('D:/work/aiproject/haftalik_bulten/spk_bulten_baslik_hiyerarsi_analizi.md', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find boundaries
dosya_bazli_start = None
alt_baslik_start = None
for i, line in enumerate(lines):
    if line.startswith('## Dosya Baz'):
        dosya_bazli_start = i
    if line.startswith('## Alt Ba'):
        alt_baslik_start = i
        break

print(f'Dosya Bazli section starts at line {dosya_bazli_start + 1}')
print(f'Alt Baslik section starts at line {alt_baslik_start + 1}')

# Process lines in the "Dosya Bazlı Hiyerarşi" section
new_lines = []
labeled_count = 0
current_section = ''

for i, line in enumerate(lines):
    if i < dosya_bazli_start or (alt_baslik_start is not None and i >= alt_baslik_start):
        new_lines.append(line)
    else:
        # Track current section header (non-indented headers)
        if line.startswith('- Sayfa') and '`' in line:
            m = re.search(r'`[A-Z]\.`\s+(.*)', line)
            if m:
                current_section = m.group(1).strip()

        # Process sub-heading lines
        if line.startswith('  - Sayfa') and '`' in line:
            if 'Alt ba' in line and 'bulunamad' in line:
                new_lines.append(line)
            else:
                label = classify_line(line, current_section)
                new_lines.append(line + ' ' + label)
                labeled_count += 1
        else:
            new_lines.append(line)

print(f'Labeled: {labeled_count} lines')

# Write result
new_content = '\n'.join(new_lines)
with open('D:/work/aiproject/haftalik_bulten/spk_bulten_baslik_hiyerarsi_analizi_labeled.md', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Written to labeled file')

# Count by label
label_counts = {}
for line in new_lines[dosya_bazli_start:alt_baslik_start]:
    if line.startswith('  - Sayfa') and '`' in line:
        m = re.search(r'\[([^\]]+)\]$', line)
        if m:
            lbl = m.group(1)
            label_counts[lbl] = label_counts.get(lbl, 0) + 1

print('\nLabel distribution:')
for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f'  {label}: {count}')

# Show Diger lines for inspection
print('\n[Diger] lines:')
diger_count = 0
for i, line in enumerate(new_lines[dosya_bazli_start:alt_baslik_start], start=dosya_bazli_start):
    if line.startswith('  - Sayfa') and '[Diğer]' in line:
        print(f'  L{i+1}: {line[:120]}')
        diger_count += 1
print(f'Total [Diger]: {diger_count}')
