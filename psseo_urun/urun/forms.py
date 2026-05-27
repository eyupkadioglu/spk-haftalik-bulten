from django import forms
from .models import Urun


class UrunForm(forms.ModelForm):
    class Meta:
        model   = Urun
        fields  = ['urun_kodu', 'marka', 'ad', 'kategori', 'barkod', 'fiyat',
                   'kaynak_url', 'ham_aciklama', 'teknik_ozellik', 'tedarikci_kodu']
        widgets = {
            'ham_aciklama':   forms.Textarea(attrs={'rows': 4}),
            'teknik_ozellik': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'urun_kodu':      'Ürün Kodu',
            'marka':          'Marka',
            'ad':             'Ürün Adı',
            'kategori':       'Kategori',
            'barkod':         'Barkod (EAN)',
            'fiyat':          'Fiyat',
            'kaynak_url':     'Kaynak URL (ürünün sayfası)',
            'ham_aciklama':   'Ham Açıklama (tedarikçi metni)',
            'teknik_ozellik': 'Teknik Özellikler',
            'tedarikci_kodu': 'Tedarikçi Kodu',
        }


class UrunImportForm(forms.Form):
    dosya = forms.FileField(label='Excel Dosyası (.xlsx)',
                            help_text='Sütunlar: urun_kodu, marka, ad, ham_aciklama, teknik_ozellik, kaynak_url')
