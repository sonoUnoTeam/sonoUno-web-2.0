from django.urls import path

from django.urls import path,include

from . import views

app_name = "sonif1D"
urlpatterns = [
    # ex: /sonif1D/
    path("index", views.index, name="index"),
    # ex: /sonif1D/inicio
    path("inicio", views.inicio, name="inicio"),
    # ex: /sonif1D/ayuda
    path("ayuda", views.ayuda, name="ayuda"),
    # ex: /sonif1D/sonido
    path("sonido", views.sonify_seno, name="sonido"),
    # ex: /sonif1D/grafico
    path("grafico", views.plot_seno, name="grafico"),
    # ex: /sonif1D/funciones_matematicas
    path("funciones_matematicas", views.funciones_matematicas, name="funciones_matematicas"),

    path("test", views.test, name="test"),

    path("test2", views.test2, name="test2"),
]