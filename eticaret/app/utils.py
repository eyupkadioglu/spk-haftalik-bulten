from datetime import datetime, date
from decimal import Decimal


_PB_SEMBOL = {'TRY': '₺', 'USD': '$', 'EUR': '€'}


def format_para(tutar, para_birimi='TRY', prefix=None):
    if tutar is None:
        tutar = 0
    val = float(tutar)
    formatted = f'{val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    if prefix is not None:
        return f'{formatted} {prefix}'.strip() if prefix else formatted
    pb = str(para_birimi or 'TRY').upper()
    sembol = _PB_SEMBOL.get(pb, pb)
    return f'{formatted} {sembol}'


def format_tarih(d):
    if isinstance(d, (date, datetime)):
        return d.strftime('%d.%m.%Y')
    return ''


def next_sequence(prefix, model, field):
    year = datetime.now().year
    count = model.query.filter(
        getattr(model, field).like(f'{prefix}-{year}-%')
    ).count()
    return f'{prefix}-{year}-{str(count + 1).zfill(5)}'


def format_miktar(v):
    if v is None:
        return '0'
    f = float(v)
    if f == int(f):
        return str(int(f))
    return f'{f:g}'


def register_template_filters(app):
    app.jinja_env.filters['format_para'] = format_para
    app.jinja_env.filters['format_tarih'] = format_tarih
    app.jinja_env.filters['format_miktar'] = format_miktar
