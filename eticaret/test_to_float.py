import sys; sys.path.insert(0, '.')
from app.blueprints.import_export.routes import _to_float

cases = [
    ("2.000",    2000.0, "TR binlik 2.000 = 2000"),
    ("2",        2.0,    "sade sayi"),
    ("2.5",      2.5,    "Ingilizce ondalik"),
    ("2,5",      2.5,    "TR ondalik"),
    ("1.234,56", 1234.56,"TR para formati"),
    ("1.234.567",1234567.0,"cok noktali TR"),
    ("100,00",   100.0,  "TR para 100"),
    ("150,00",   150.0,  "TR para 150"),
    (2000,       2000.0, "openpyxl numeric"),
    (2,          2.0,    "openpyxl int"),
    (2.5,        2.5,    "openpyxl float"),
]
ok = fail = 0
for val, expected, desc in cases:
    got = _to_float(val)
    status = "OK" if abs(got - expected) < 0.0001 else "FAIL"
    if status == "FAIL": fail += 1
    else: ok += 1
    print(status, str(val), "=>", got, "(beklenen", expected, ")", desc)
print(ok, "OK,", fail, "FAIL")
