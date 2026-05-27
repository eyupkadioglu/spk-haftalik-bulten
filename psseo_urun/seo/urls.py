from django.urls import path
from . import views

app_name = 'seo'

urlpatterns = [
    path('<int:urun_id>/uret/',          views.seo_uret,        name='uret'),
    path('<int:urun_id>/toplu/',         views.seo_toplu_uret,  name='toplu'),
    path('<int:icerik_id>/onayla/',      views.seo_onayla,      name='onayla'),
    path('<int:icerik_id>/reddet/',      views.seo_reddet,      name='reddet'),
    path('export/',                      views.seo_export,      name='export'),
    path('prestashop-export/',           views.prestashop_export, name='ps_export'),
]
