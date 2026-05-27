# Bagimsiz SPK Haftalik Bulten Uygulama Plani

## 1. Ozet

Bu plan, SPK'nin haftalik olarak yayimladigi bultenin daireler, ilgili KBY'ler ve Kurul Baskani arasinda kontrollu, izlenebilir ve arsivlenebilir bir surecle uretilmesini tarif eder.

Yeni calisma alani `D:\work\aiproject\haftalik_bulten` klasorudur. Bu klasor EBYS klasorunden bagimsizdir; EBYS altindaki mevcut dosyalar degistirilmez.

Hedef surec:

- Her hafta icin tek bir haftalik bulten kaydi acilir.
- Her daire kendi bulten bolumunu metin ve tablo olarak bagimsiz hazirlar.
- Her bolum ilgili KBY tarafindan onaylanir veya gerekceli olarak iade edilir.
- KBY onayli bolumler sistem tarafindan butunlesik bulten taslagina alinir.
- Tum zorunlu bolumler KBY onayindan gecmeden Kurul Baskani nihai onayina gonderilmez.
- Kurul Baskani butunlesik bulteni onayladiginda temiz PDF uretilir, loglu bulten gorunumu saklanir ve kayit arsive alinir.

## 2. Klasor ve Dosya Yapisi

Baslangic kapsaminda olusturulacak yapi:

```text
haftalik_bulten/
  README.md
  implementation_plan.md
```

Ileride uygulama koduna gecildiginde bu klasor kendi veri modeli, arayuzleri, servisleri, testleri ve arsivleme mantigiyla bagimsiz bir modul olarak ilerlemelidir.

## 3. SPK Teskilat Esasli Organizasyon

Bu modulde daire, KBY ve Kurul Baskani akislari SPK'nin resmi teskilat sayfasindaki hiyerarsiye gore modellenir.

Kaynaklar:

- Teskilat: https://www.spk.gov.tr/hakkimizda/organizasyon/teskilat
- Kurul Baskan Yardimcilari: https://spk.gov.tr/hakkimizda/organizasyon/teskilat/kurul-baskan-yardimcilari
- Daire Baskanliklari: https://spk.gov.tr/hakkimizda/organizasyon/teskilat/daire-baskanliklari

### 3.1 Ust hiyerarsi

- Kurul Karar Organi
- Kurul Baskani
- Kurul Baskan Yardimcilari
- Daire Baskanliklari

Resmi sayfada Kurul Baskan Yardimcilari olarak su isimler yer almaktadir:

- Ugur YAYLAONU
- Ali ERDURMUS
- Ender KURTULAN
- Aytac DIKMEN

### 3.2 Daire baskanliklari

Haftalik bulten bolum sahipligi ve KBY onay eslesmeleri asagidaki daire baskanliklari uzerinden tanimlanir:

- Aracilik Faaliyetleri Dairesi Baskanligi
- Bagimsiz Denetim ve Degerleme Faaliyetleri Dairesi Baskanligi
- Denetleme Dairesi Baskanligi
- Finansal Teknolojiler Dairesi Baskanligi
- Katilim Finansmani Dairesi Baskanligi
- Ortakliklar Finansmani Dairesi Baskanligi
- Piyasa Gozetim ve Denetim Dairesi Baskanligi
- Uluslararasi Iliskiler ve Surdurulebilirlik Dairesi Baskanligi
- Yatirim Fonlari Dairesi Baskanligi
- Yatirim Ortakliklari Dairesi Baskanligi
- Hukuk Isleri Dairesi Baskanligi
- Strateji Gelistirme Dairesi Baskanligi
- Bilgi Sistemleri Dairesi Baskanligi
- Destek Hizmetleri Dairesi Baskanligi
- Insan Kaynaklari ve Egitim Dairesi Baskanligi
- Kurumsal Iletisim Dairesi Baskanligi

### 3.3 Bulten surecine etkisi

- Her daire baskanligi sistemde bir `Daire Başkanlığı` kaydi olarak tanimlanir.
- Her daire icin haftalik bultende zorunlu, opsiyonel veya pasif bolum ayari yapilabilir.
- Her daire bir veya daha fazla KBY ile eslestirilir.
- KBY eslesmesi olmadan daire bolumu Kurul Baskani onay surecine ilerleyemez.
- Daire ve KBY eslesmeleri arsiv kaydinda yayin haftasindaki haliyle saklanir; daha sonra organizasyon degisse bile eski bultenin onay zinciri korunur.

## 4. Kullanicilar, Roller ve Yetkiler

Sistem kullanicilari asagidaki kurumsal rol hiyerarsisine gore tanimlanir:

- `DBY`: Daire Baskan Yardimcisi
- `DB`: Daire Baskani
- `KBY`: Kurul Baskan Yardimcisi
- `KOB`: Kurul Ozel Burosu (KOB_PERSONELI ile birlikte)
- `KB`: Kurul Baskani
- `ADMIN`: Sistem yoneticisi / arsiv yetkilisi

### DBY

- Kayit girebilir, mevcut kaydi duzenleyebilir.
- Onaya gonderilmemis kendi kaydini silebilir (DRAFT veya IADE durumundaki, createdBy === kendi id'si).
- Kaydi DB onayina gonderir. Gonderilen kayit uzerinde artik degisiklik yapamaz.
- DB herhangi bir islem yapmadan once (kaydetme, duzeltme, onaya gonderme) DBY onaya gonderme islemini geri cekebilir (DBY_RETRACT).

### DB

- Kayit girebilir, mevcut kaydi duzenleyebilir.
- Onaya gonderilmemis kayitlari silebilir (DRAFT veya IADE durumundaki kayitlar).
- Mevcut kaydi DBY'ye iade edebilir (DB_RETURN → SECTION_PREP).
- Kaydi KBY onayina gonderir. Gonderilen kayit uzerinde artik degisiklik yapamaz.
- KBY herhangi bir islem yapmadan once DB onaya gonderme islemini geri cekebilir (DB_RETRACT).

### KBY

- Kayit girebilir, mevcut kaydi duzenleyebilir.
- Mevcut kaydi DB'ye iade edebilir (KBY_RETURN → DB_APPROVAL asamasina doner).
- Kaydi KB onayina (KOB paketi) gonderir. Gonderilen kayit uzerinde artik degisiklik yapamaz.
- KB herhangi bir islem yapmadan once KBY onaya gonderme islemini geri cekebilir (KBY_RETRACT).

### KOB

- Mevcut kayitlari her asamada gorebilir; dogrudan icerik degisikligi yapamaz.
- Her asamada yorum veya oneri ekleyebilir (KOB_SUGGEST). Oneriler baglayici degildir.
- Kurul Baskani onayina gidecek nihai paketin tamligini ve siralamasini kontrol eder.

### KB

- Butunlesik bulteni nihai olarak onaylar.
- KB onayiyla haftalik bulten tamamlanmis olur ve yayimlanir.
- Yayim sonrasinda icerik kilitlenir; degisiklik yapilamaz.

### Sistem yoneticisi / arsiv yetkilisi

- Kullanici, daire, KBY ve yetki eslesmelerini tanimlar.
- Yayimlanmis bultenleri ve loglu arsiv kayitlarini goruntuler.
- Yayimlanmis bulten icerigini degistiremez; yalnizca yetki dahilinde arsiv ve log sorgulama yapar.

## 5. Ana Is Akisi

### 5.1 Haftalik bulten acma

- Yetkili kullanici ilgili hafta ve yil icin yeni bulten kaydi acar.
- Sistem ayni hafta/yil icin ikinci aktif bulten acilmasini engeller.
- Bultene dahil olacak daireler ve zorunlu bolumler secilir.
- Her daire icin baslangic durumunda bir bolum kaydi olusturulur.

### 5.2 Daire bolumu hazirlama (SECTION_PREP)

- DBY kendi dairesine ait bolume kayit girer; kayitlari duzenler; onaya gonderilmemis kendi kayitlarini siler.
- Sistem her kaydetmede eski ve yeni icerigi loglar (kimin ne degistirdigi kayit altinda).
- DBY hazirlik tamamlandiginda bolumu `DB Onayi Bekliyor` durumuna gonderir (DBY_APPROVE).
- Gonderim sonrasinda DBY artik icerik degistiremez. Ancak DB herhangi bir islem yapmadan once DBY geri cekme islemi yapabilir (DBY_RETRACT → SECTION_PREP).

### 5.3 DB onayi (DB_APPROVAL)

- DB bolum kayitlarini inceleyebilir, duzenleyebilir, onaya gonderilmemis kayitlari silebilir.
- DB uygun buldugu bolumu `KBY Onayi Bekliyor` durumuna gonderir (DB_APPROVE).
- DB eksik veya hata tespit ederse gerekceyle DBY'ye iade eder (DB_RETURN → SECTION_PREP).
- DB gonderim sonrasinda artik icerik degistiremez. Ancak KBY herhangi bir islem yapmadan once DB geri cekme islemi yapabilir (DB_RETRACT → DB_APPROVAL).

### 5.4 KBY onayi (KBY_APPROVAL)

- KBY bolum kayitlarini inceleyebilir, duzenleyebilir.
- KBY bolumu KOB paketine gonderir (KBY_APPROVE → KBY_APPROVED → KOB_READY).
- KBY eksik veya hata tespit ederse gerekceyle DB'ye iade eder (KBY_RETURN → DB_APPROVAL).
- KBY gonderim sonrasinda artik icerik degistiremez. Ancak KB herhangi bir islem yapmadan once KBY geri cekme islemi yapabilir (KBY_RETRACT → KBY_APPROVAL).
- Her onay, iade ve geri cekme isleminde kullanici, tarih, saat, gerekce ve bolum surumu loglanir.

### 5.5 Butunlestirme

- Sistem KBY onayli bolumleri belirlenen siraya gore butunlesik bulten taslagina alir.
- Henuz onaylanmamis bolumler butunlesik nihai taslaga dahil edilmez.
- Tum zorunlu bolumler KBY onayi aldiginda bulten `KOB Kontrolu Bekliyor` durumuna gecer.

### 5.6 KOB paket kontrolu

- KOB her asamada bolumleri goruntüleyebilir; dogrudan icerik degisikligi yapamaz.
- KOB herhangi bir asamada yorum veya oneri ekleyebilir; oneriler baglayici degildir, icerik sahibi isler.
- KOB butunlesik bulteni, onay zincirini, bolum siralamasini, PDF taslagini ve loglu gorunumu kontrol eder.
- KOB uygun bulursa bulteni `Baskan Onayi Bekliyor` durumuna gonderir.
- KOB eksik veya hata tespit ederse zorunlu gerekceyle ilgili asamaya iade eder.

### 5.7 Kurul Baskani nihai onayi

- Kurul Baskani butunlesik bulteni tek dokuman olarak gorur.
- Baskan onay verirse bulten `Yayimlandi` durumuna gecer.
- Baskan iade ederse iade gerekcesiyle birlikte bulten ilgili bolumlere veya koordinasyon sorumlusuna geri doner.
- Baskan onayi sonrasinda icerik kilitlenir.

### 5.8 PDF uretimi ve arsivleme

- Temiz yayim PDF'i uretilir.
- Kurum ici inceleme icin loglu bulten gorunumu uretilir.
- Bolum surumleri, onay bilgileri, degisiklik loglari ve PDF kayitlari birlikte arsivlenir.
- Arsiv kaydi silinmez; sonradan duzeltme gerekiyorsa yeni revizyon veya ek bulten kaydi olusturulur.

## 6. Durum Modeli

Bulten ana durumlari:

- `Taslak`
- `Daire Hazirliginda`
- `KBY Onaylari Bekleniyor`
- `KOB Kontrolu Bekliyor`
- `Baskan Onayi Bekliyor`
- `Yayimlandi`
- `Iade Edildi`
- `Arsivlendi`

Bolum durumlari:

- `Bos`
- `Daire Hazirliginda`
- `DBY Kontrolu Bekliyor`
- `DB Onayi Bekliyor`
- `KBY Onayi Bekliyor`
- `Daire Revizyonunda`
- `DB Onaylandi`
- `KBY Onaylandi`
- `KOB Paket Kontrolunde`
- `Butunlesik Bultene Alindi`
- `Kilitli`

## 7. Veri Modeli

### WeeklyBulletin

- `id`
- `year`
- `weekNumber`
- `title`
- `status`
- `createdBy`
- `createdAt`
- `submittedToChairAt`
- `approvedByChairAt`
- `publishedAt`
- `archiveRecordId`

### BulletinUser

- `id`
- `fullName`
- `title`
- `roleCode`
- `departmentId`
- `departmentName`
- `reportsToUserId`
- `isActive`
- `validFrom`
- `validTo`

### BulletinRole

- `code`
- `name`
- `level`
- `canEditSection`
- `canSubmitToDby`
- `canDbyReview`
- `canDbApprove`
- `canKbyApprove`
- `canKobPackageReview`
- `canChairApprove`
- `canViewArchive`

### BulletinSection

- `id`
- `bulletinId`
- `departmentId`
- `departmentName`
- `departmentOfficialName`
- `responsibleKbyUserId`
- `responsibleKbyName`
- `responsibleKbyTitle`
- `title`
- `order`
- `contentHtml`
- `tables`
- `attachments`
- `status`
- `preparedBy`
- `lastEditedBy`
- `reviewedByDby`
- `reviewedByDbyAt`
- `approvedByDb`
- `approvedByDbAt`
- `submittedToKbyAt`
- `approvedByKby`
- `approvedByKbyAt`
- `rejectionReason`
- `version`

### BulletinApproval

- `id`
- `bulletinId`
- `sectionId`
- `approvalType`: `DBY_REVIEW`, `DB_APPROVAL`, `KBY_APPROVAL`, `KOB_PACKAGE_REVIEW`, `KB_FINAL_APPROVAL`
- `approverUserId`
- `approverName`
- `approverRoleCode`
- `decision`
- `decisionAt`
- `comment`
- `sectionVersion`

### BulletinChangeLog

- `id`
- `bulletinId`
- `sectionId`
- `actorUserId`
- `actorName`
- `actorRole`
- `actionType`
- `fieldName`
- `oldValueSummary`
- `newValueSummary`
- `reason`
- `createdAt`
- `versionBefore`
- `versionAfter`

### BulletinArchiveRecord

- `id`
- `bulletinId`
- `year`
- `weekNumber`
- `publishedPdfPath`
- `loggedViewPath`
- `snapshotJsonPath`
- `publishedAt`
- `approvedByChair`
- `organizationSnapshot`
- `searchKeywords`

### Department

- `id`
- `officialName`
- `status`
- `isRequiredForWeeklyBulletin`
- `responsibleKbyUserIds`
- `displayOrder`
- `sourceUrl`
- `validFrom`
- `validTo`

### OrganizationSnapshot

- `id`
- `bulletinId`
- `capturedAt`
- `chairUserId`
- `chairName`
- `kobReviewUserId`
- `kobReviewUserName`
- `kbyAssignments`
- `departmentAssignments`
- `sourceUrls`

## 7b. Başlık Grubu Şablonu

Bülten içeriği 8 ana grup ve 58 alt gruba göre sınıflandırılır. Ana grup kodu tek harf; alt grup kodları pozisyonel (A01, A02…).

| Kod | Ana Başlık | Alt Grup Sayısı |
|-----|-----------|----------------|
| A | İzahname / İhraç Belgesi Onaylanan Sermaye Piyasası Araçları | 6 (A01–A06) |
| B | Yeni Faaliyet İzinleri | 15 (B01–B15) |
| C | Suç Duyurusu, İdari Para Cezası ile Diğer Yaptırım ve Tedbirler | 5 (C01–C05) |
| D | Sermaye Piyasası Kurumlarının Diğer Başvuru Sonuçları | 19 (D01–D19) |
| E | Halka Açık Ortaklıkların Diğer Başvuru Sonuçları | 6 (E01–E06) |
| F | Sermaye Piyasası Kurumlarının Ortaklık Yapısı Değişiklikleri | 4 (F01–F04) |
| G | Duyuru ve İlke Kararları | 2 (G01–G02) |
| H | Diğer Özel Durumlar | 1 (H01) |

**Notlar:**
- Gruplar ve alt gruplar admin ekranından sürükle-bırak ile yeniden sıralanabilir.
- Alt grup görüntü kodu (A01, A02…) pozisyona göre üretilir; depolanan kod değişmez.
- Bülten ön izlemesinde: ana gruplar Romen rakamı (I, II…), alt gruplar küçük harf (a, b…), kayıtlar rakam (1, 2…) ile numaralandırılır.
- Sadece tablo içeren kayıtlar sıra numarası almaz.

## 8. Log ve Denetim Izi Kurallari

Loglanacak islemler:

- Bulten olusturma
- Bolum olusturma
- Metin ekleme, duzenleme ve silme
- Tablo ekleme, satir ekleme, satir silme ve hucre degistirme
- Ek dosya ekleme ve cikarma
- Uzman/Uzman Yardimcisi tarafindan DBY kontrolune gonderme
- DBY kontrol onayi
- DBY iadesi
- DB onayi
- DB iadesi
- KBY onayina gonderme
- KBY onayi
- KBY iadesi
- KOB paket kontrolune gonderme
- KOB paket kontrol onayi
- KOB iadesi
- Bulten butunlestirme
- Baskan onayina gonderme
- Baskan onayi
- Baskan iadesi
- PDF uretimi
- Yayimlama
- Arsivleme
- Daire/KBY eslesmesi degisikligi
- Organizasyon snapshot alma

Log kayitlari sadece teknik takip icin degil, gelecekte sorgu ve arastirmalarda kullanilacak islevsel gecmis olarak saklanmalidir.

## 9. Arsiv ve Sorgulama

Arsivde birlikte saklanacak kayitlar:

- Temiz yayimlanmis PDF
- Loglu bulten gorunumu
- Tum bolumlerin yayin anindaki son halleri
- Bolum surum gecmisi
- DBY, DB, KBY, KOB ve Kurul Baskani onay/kontrol kayitlari
- Tum degisiklik loglari
- Yayin haftasinda gecerli olan SPK teskilat ve daire/KBY eslesme snapshot'i

Sorgu alanlari:

- Yil ve hafta
- Daire
- Konu/baslik
- Metin icerigi
- Tablo alanlari
- Hazirlayan kullanici
- DBY kontrol eden kullanici
- DB onaycisi
- KBY onaycisi
- KOB kontrol eden kullanici
- Kurul Baskani onay bilgisi
- Islem turu
- Tarih araligi
- Daire/KBY eslesmesi
- Organizasyon snapshot tarihi

## 10. Arayuz Ihtiyaclari

Planlanan ekranlar:

- Haftalik bulten listesi
- Yeni haftalik bulten olusturma ekrani
- Daire bolum editoru
- Tablo editoru
- DBY kontrol ve iade ekrani
- DB onay ve iade ekrani
- KBY onay ve iade ekrani
- KOB paket kontrol ve iade ekrani
- Butunlesik bulten onizleme ekrani
- Kurul Baskani nihai onay ekrani
- PDF uretim ve yayimlama ekrani
- Loglu bulten gorunumu
- Arsiv ve gelismis arama ekrani
- Organizasyon ve daire/KBY eslesme yonetimi ekrani

## 11. Test Plani

Elle dogrulanacak ana senaryolar:

- SPK resmi teskilat sayfasindan alinan daire baskanliklarinin sistemde department olarak tanimli olmasi.
- Daire/KBY eslesmesi olmayan bolumun Baskan onayina ilerleyememesi.
- Yeni hafta bulteni olusturma.
- Birden fazla dairenin ayni hafta bagimsiz bolum hazirlamasi.
- Uzman/Uzman Yardimcisinin yalnizca kendi daire bolumunu duzenleyebilmesi.
- DBY'nin kendi dairesindeki bolumu kontrol edip DB onayina gonderebilmesi.
- DBY'nin hatali bolumu gerekceyle Uzman/Uzman Yardimcisina iade edebilmesi.
- DB'nin kendi dairesindeki bolumu onaylayip KBY onayina gonderebilmesi.
- DB onayi olmayan bolumun KBY onayina ilerleyememesi.
- KBY'nin kendi bolumunu onaylamasi.
- KBY'nin yetkili olmadigi bolumde islem yapamamasi.
- KBY iadesinde bolumun ilgili daireye geri donmesi ve iade gerekcesinin loglanmasi.
- KOB'un KBY onaylari tamamlanan butunlesik bulteni kontrol edip Baskan onayina gonderebilmesi.
- KOB kontrolu tamamlanmadan Kurul Baskani onayinin acilmamasi.
- Metin degisikligi, tablo degisikligi, ekleme ve cikarma islemlerinde log olusmasi.
- Tum KBY onaylari tamamlanmadan Kurul Baskani onayinin acilmamasi.
- KBY onaylari tamamlaninca butunlesik bultenin Kurul Baskani onune gelmesi.
- Baskan onayi sonrasi PDF uretimi, yayimlama, kilitleme ve arsivleme.
- Yayinlanmis bultende icerik degisikliginin engellenmesi.
- Loglu bulten gorunumunde tum degisiklik gecmisinin eksiksiz izlenmesi.
- Arsivde hafta, daire, konu, kullanici ve islem turune gore sorgulama yapilmasi.
- Yayinlanan bultenin arsivinde organizasyon snapshot'inin korunmasi.

## 12. Varsayimlar

- Klasor adi `haftalik_bulten` olarak belirlenmistir.
- Bu calisma EBYS klasorunden bagimsizdir.
- Ilk teslimat uygulama kodu degil, karar tamamlanmis plan dokumantasyonudur.
- KBY onaylari bolum bazli zorunlu ara onaydir.
- Kurul Baskani tek nihai onay makamidir.
- Baskan onayindan sonra bulten kilitlenir ve arsive alinir.
- Duzeltme ihtiyaci yayin sonrasi mevcut kaydi degistirmek yerine revizyon veya ek bulten sureciyle ele alinacaktir.
- Daire baskanliklari ve KBY listesi resmi SPK teskilat sayfasindan periyodik olarak kontrol edilmelidir; plan olusturma tarihinde kaynak olarak SPK web sitesi esas alinmistir.
