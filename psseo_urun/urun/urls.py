from django.urls import path
from . import views

app_name = 'urun'

urlpatterns = [
    path('',                  views.urun_liste,   name='liste'),
    path('ekle/',             views.urun_ekle,    name='ekle'),
    path('<int:pk>/',         views.urun_detay,   name='detay'),
    path('<int:pk>/duzenle/', views.urun_duzenle, name='duzenle'),
    path('<int:pk>/sil/',     views.urun_sil,     name='sil'),
    path('import/',           views.urun_import,  name='import'),
    path('export/',           views.urun_export,  name='export'),
    path('scrape/',           views.urun_scrape,  name='scrape'),
]
