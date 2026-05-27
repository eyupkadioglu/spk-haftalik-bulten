from app import create_app
app = create_app()
with app.test_client() as c:
    with app.app_context():
        from app.models.user import User
        u = User.query.first()
        if u:
            with c.session_transaction() as sess:
                sess['_user_id'] = str(u.id)
                sess['_fresh'] = True
    for path in ['/import-export/', '/import-export/sablon/stok', '/import-export/sablon/resim']:
        r = c.get(path)
        print(f"{path}: {r.status_code}")
