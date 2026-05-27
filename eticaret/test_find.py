import sys; sys.path.insert(0, '.')
from app.blueprints.import_export.routes import _find

tests = [
    ({'Para Birimi': 'EUR'}, 'alas para birimi', 'alis para birimi', 'para birimi'),
    ({'Alis Para Birimi (TRY/USD/EUR)': 'USD'}, 'alis para birimi'),
    ({'Alis Para Birimi': 'EUR'}, 'alis para birimi'),
    ({'satis para birimi': 'USD'}, 'satis para birimi'),
    ({'PARA BIRIMI': 'EUR'}, 'para birimi'),
]
for row, *keys in tests:
    result = _find(row, *keys)
    print(list(row.keys())[0], '/', keys[0], '=>', result)
