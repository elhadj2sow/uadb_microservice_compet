
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('inscription.urls')),
    # Routes de retour PayTech (success/cancel)
    path('paiement/success', lambda request: HttpResponse("<h2>Paiement réussi !</h2>", content_type="text/html")),
    path('paiement/cancel', lambda request: HttpResponse("<h2>Paiement annulé.</h2>", content_type="text/html")),
]
