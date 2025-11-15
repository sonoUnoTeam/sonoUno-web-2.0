from django.urls import path

from django.urls import path,include

from . import views

app_name = "muongraphy"
urlpatterns = [

    path("index", views.index, name="index"),
    path('grafico/<str:file_name>/', views.grafico, name='grafico'),

]