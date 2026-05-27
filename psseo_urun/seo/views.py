import io
import csv
import openpyxl
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from urun.models import Urun
from .models import SeoIcerik

TUM_TIPLER = ['urun_adi', 'ozet', 'detay', 'meta_baslik', 'meta_aciklama', 'anahtar_kelime']


def seo_uret(request, urun_id):
    urun   = get_object_or_404(Urun, pk=urun_id)
    tip    = request.POST.get('tip', 'ozet')
    kaynak = request.POST.get('kaynak', 'ai')

    try:
        if kaynak == 'ai':
            from .services.ai_service import uret_ai_icerik
            icerik, model_adi = uret_ai_icerik(urun, tip)
        elif kaynak == 'chatgpt':
            from .services.openai_service import uret_openai_icerik
            icerik, model_adi = uret_openai_icerik(urun, tip)
        else:
            from .services.template_service import uret_sablon_icerik
            icerik    = uret_sablon_icerik(urun, tip)
            model_adi = ''

        SeoIcerik.objects.create(
            urun=urun, tip=tip, icerik=icerik,
            kaynak=kaynak, model_adi=model_adi
        )
        messages.success(request, f'İçerik üretildi ({tip}, {kaynak}).')
    except Exception as e:
        messages.error(request, f'Hata: {e}')

    return redirect('urun:detay', pk=urun_id)


def seo_toplu_uret(request, urun_id):
    urun   = get_object_or_404(Urun, pk=urun_id)
    kaynak = request.POST.get('kaynak', 'ai')
    tipler = request.POST.getlist('tipler') or TUM_TIPLER
    basarili = 0
    for tip in tipler:
        try:
            if kaynak == 'ai':
                from .services.ai_service import uret_ai_icerik
                icerik, model_adi = uret_ai_icerik(urun, tip)
            elif kaynak == 'chatgpt':
                from .services.openai_service import uret_openai_icerik
                icerik, model_adi = uret_openai_icerik(urun, tip)
            else:
                from .services.template_service import uret_sablon_icerik
                icerik    = uret_sablon_icerik(urun, tip)
                model_adi = ''
            SeoIcerik.objects.create(
                urun=urun, tip=tip, icerik=icerik,
                kaynak=kaynak, model_adi=model_adi
            )
            basarili += 1
        except Exception as e:
            messages.error(request, f'{tip} hatası: {e}')

    if basarili:
        messages.success(request, f'{basarili} içerik üretildi.')
    return redirect('urun:detay', pk=urun_id)


@require_POST
def seo_onayla(request, icerik_id):
    icerik = get_object_or_404(SeoIcerik, pk=icerik_id)
    # Aynı tip önceki onayları kaldır
    SeoIcerik.objects.filter(urun=icerik.urun, tip=icerik.tip, onaylandi=True).update(onaylandi=False)
    icerik.onaylandi = True
    icerik.save()
    messages.success(request, 'İçerik onaylandı.')
    return redirect('urun:detay', pk=icerik.urun_id)


@require_POST
def seo_reddet(request, icerik_id):
    icerik = get_object_or_404(SeoIcerik, pk=icerik_id)
    icerik.onaylandi = False
    icerik.save()
    messages.info(request, 'Onay kaldırıldı.')
    return redirect('urun:detay', pk=icerik.urun_id)


def seo_export(request):
    """Onaylanan SEO içeriklerini Excel'e aktar."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'SEO İçerikler'
    ws.append(['urun_kodu', 'marka', 'ad', 'tip', 'kaynak', 'icerik', 'olusturulma'])
    for ic in SeoIcerik.objects.filter(onaylandi=True).select_related('urun'):
        ws.append([
            ic.urun.urun_kodu, ic.urun.marka, ic.urun.ad,
            ic.tip, ic.kaynak, ic.icerik,
            ic.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="seo_icerikleri.xlsx"'
    return resp


def prestashop_export(request):
    """
    PrestaShop 1.7 CSV import formatında onaylı içerikleri aktar.
    Sütunlar: ID;Name;Short description;Description;Meta title;Meta description;Meta keywords
    """
    urun_ids   = request.GET.getlist('urun') or None
    urunler_qs = Urun.objects.prefetch_related('seo_icerikleri')
    if urun_ids:
        urunler_qs = urunler_qs.filter(pk__in=urun_ids)

    buf = io.StringIO()
    # PrestaShop CSV: ; ayraç, UTF-8 BOM
    yazar = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_ALL)
    yazar.writerow(['Product ID', 'Reference', 'Name', 'Short description',
                    'Description', 'Meta title', 'Meta description', 'Tags'])

    for urun in urunler_qs:
        def onaylandi(tip):
            return urun.seo_icerikleri.filter(tip=tip, onaylandi=True).values_list('icerik', flat=True).first() or ''

        yazar.writerow([
            '',                  # Product ID (PrestaShop dolduracak)
            urun.urun_kodu,
            urun.ad,
            onaylandi('ozet'),
            onaylandi('detay'),
            onaylandi('meta_baslik'),
            onaylandi('meta_aciklama'),
            onaylandi('anahtar_kelime'),
        ])

    csv_bytes = '﻿' + buf.getvalue()  # UTF-8 BOM — Excel uyumu
    resp = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="prestashop_import.csv"'
    return resp
