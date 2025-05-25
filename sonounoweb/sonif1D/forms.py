from django import forms

# Formulario para la carga de un archivo
class ArchivoForm(forms.Form):
    archivo = forms.FileField(label='Selecciona un archivo')

# Formulario para la configuración del gráfico
class ConfiguracionGraficoForm(forms.Form):
    grilla = forms.BooleanField(required=False, label='Grilla')
    escala_grises = forms.BooleanField(required=False, label='Escala de grises')
    rotar_eje_x = forms.BooleanField(required=False, label='Rotar eje X')
    rotar_eje_y = forms.BooleanField(required=False, label='Rotar eje Y')
    ESTILO_LINEA_CHOICES = [
        ('solid', 'Sólido'),
        ('dot', 'Punto'),
        ('dash', 'Guion'),
        ('longdash', 'Guion Largo'),
        ('dashdot', 'Guion Punto'),
        ('longdashdot', 'Guion Largo Punto'),
    ]
    estilo_linea = forms.ChoiceField(
        choices=ESTILO_LINEA_CHOICES,
        widget=forms.RadioSelect,
        label='Estilo de línea',
        initial='solid'
    )
    color_linea = forms.ChoiceField(
        choices=[
            ('blue', 'Azul'),
            ('red', 'Rojo'),
            ('green', 'Verde'),
            ('black', 'Negro'),
            ('yellow', 'Amarillo')
        ],
        label='Color de línea',
        initial='blue',
        widget=forms.RadioSelect,
    )
    name_grafic = forms.CharField(label='Nombre de Grafico')
    name_eje_x = forms.CharField(label='Nombre de Eje X')
    name_eje_y = forms.CharField(label='Nombre de Eje Y')    