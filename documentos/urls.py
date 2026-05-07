from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('ajax/objetos/', views.ajax_objetos, name='ajax_objetos'),
]
