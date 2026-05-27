# Haftalik Bulten

Bu klasor, EBYS klasorunden bagimsiz olarak SPK haftalik bulten surecinin planlanmasi icin olusturulmustur.

Amaç; dairelerin kendi bulten bolumlerini bagimsiz hazirladigi, ilgili KBY'lerin bolum bazli onay verdigi, Kurul Baskani onune yalnizca butunlesik bultenin geldigi ve yayinlanan PDF ile tum islem loglarinin arsivlendigi sureci netlestirmektir.

## Icerik

- `implementation_plan.md`: Haftalik bulten modulu icin karar tamamlanmis uygulama plani.
- `index.html`: localStorage tabanli ilk prototip uygulama.
- `css/app.css`: prototip arayuz stilleri.
- `js/app.js`: storage adapter, organizasyon, bulten, onay, log ve arsiv akislari.
- `spk_bulten_baslik_analizi.md`: `spkbulten` klasorundeki PDF'lerden cikarilan ham baslik analizi.
- `baslik_gruplandirma_referansi.md`: haftalik bulten maddeleri icin A00-G00 ana baslik ve alt baslik aileleri.
- `js/sample_pdf_bultenleri.js`: 2026 klasorunden aktarilan 5 ornek bultenin basliklari, PDF icerik metinleri ve PDF'den ayrica parse edilen tablolari.
- `spk_bulten_baslik_hiyerarsi_analizi_labeled.md`: gecmis PDF basliklarinin anlam/ailesi bazinda etiketlenmis analizi.

## Calistirma

`index.html` dosyasi dogrudan tarayicida acilabilir. Prototip verileri tarayicinin localStorage alaninda `spk_haftalik_bulten_v1` anahtariyla saklanir.

## Temel Ilkeler

- Bu klasor EBYS uygulamasindan bagimsizdir.
- EBYS altindaki dosyalar bu calisma kapsaminda degistirilmez.
- Ilk kapsam uygulama kodu degil, surec, veri modeli, yetki, log, arsiv ve test planinin dokumante edilmesidir.
- Modulun ana urun karari bulten editorunden once organizasyon kontrollu onay ve arsiv sistemi olmaktir.
- Daire baskanliklari ve KBY hiyerarsisi icin SPK'nin resmi teskilat sayfasi esas alinir.
- Organizasyon baslangic verisi 5 KBY slotu ve 16 daire baskanligi ile kurulur; resmi isim listesinde gorunmeyen KBY slotu `Bos KBY Kadrosu` olarak tutulur.
- Kullanici rolleri `Uzman/Uzman Yardimcisi`, `DBY`, `DB`, `KBY`, `KOB` ve `KB` zincirine gore modellenir.
- Organizasyon semasi yalnizca admin tarafindan surukle-birak yontemiyle kurulabilir; daireler KBY'ye veya dogrudan KB'ye admin tarafindan baglanabilir.
- Uygulama arayuzunde Turkce karakterler kullanilir.
- Organizasyon tek bir birlesik sema olarak gosterilir.
- Organizasyon semasinda daire kartlari `Dairesi` ibaresiyle gosterilir; kart icinde KBY yerine Daire Baskani adi yazilir.
- DB, DBY, Uzman, Uzman Yardimcisi ve KOB Personeli kendi bagli oldugu daire/KOB altinda gosterilir.
- Bir daireye birden fazla DBY eklenebilir.
- Daire kartlarinda personel tek tek ana semayi sisirmeden `DBY`, `Uzman`, `Buro Personeli` rol gruplari olarak ozetlenir.
- KOB kartinda tekrar eden KOB adi yazilmaz; KOB altinda `DBY` ve `Buro Personeli` rol gruplari gosterilir.
- Personel listesi `Personel Adi Soyadi`, `Dairesi`, `Rol Grubu` kolonlariyla CSV/Excel kopyala-yapistir aktarimi olarak topluca yuklenebilir.
- Haftalik bulten akisinda Uzman veya Buro Personeli veri girisi yapar; DBY, DB ve KBY kendi asamalarinda ekleme/cikarma/duzenleme yapabilir.
- Yetki devri hiyerarsiktir: DBY kendi dairesindeki alt personelin, DB kendi dairesindeki DBY ve alt personelin, KBY ise kendisine bagli dairelerdeki DB/DBY ve alt personelin bulten yetkilerini kullanabilir.
- KOB dogrudan icerik degistirmez; sadece DB/KBY tarafindan gorulecek oneriler olusturur.
- Tum KBY'ler bolumlerini onaya sundugunda toplu bulten Kurul Baskani onayina gidebilir.
- Organizasyon semasinda kullanici isimleri, unvanlari, rolleri ve daire baglantilari yalnizca admin tarafindan girilebilir.
- Admin `SPK DB adlarını getir` aksiyonuyla resmi daire detay sayfalarindan derlenen Daire Baskani adlarini akademik unvanlari temizlenmis sekilde ilgili dairelere uygulayabilir.
- Haftalik bulten acilisinda organizasyon snapshot'i alinir; sonraki organizasyon degisiklikleri acilmis veya yayimlanmis bultenlerin onay zincirini degistirmez.
- Bulten bolumleri A00-G00 baslik gruplandirma referansindaki ana baslik ve alt baslik ailelerinden biriyle etiketlenebilir.
- `spkbulten/2026` klasorundeki `2026-01.pdf` - `2026-05.pdf` dosyalari site acilisinda 5 duzenlenebilir ornek bulten olarak, basliklari, PDF'den parse edilen icerikleri ve tablolariyla aktarilir; PDF footer/adres alani aktarilmaz.
