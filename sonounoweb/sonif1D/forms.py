from django import forms

# Formulario para la carga de un archivo
class ArchivoForm(forms.Form):
    archivo = forms.FileField(label='Selecciona un archivo')

# Formulario para la configuración del gráfico
class ConfiguracionGraficoForm(forms.Form):
    grilla = forms.BooleanField(
        required=False, 
        label='Mostrar grilla',
        initial=True,
        help_text='Muestra líneas de cuadrícula en el gráfico'
    )
    escala_grises = forms.BooleanField(
        required=False, 
        label='Escala de grises',
        initial=False,
        help_text='Convierte el gráfico a escala de grises'
    )

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
    name_grafic = forms.CharField(
        label='Nombre de Gráfico',
        initial='Gráfico de Datos',
        max_length=100,
        help_text='Título que aparecerá en la parte superior del gráfico'
    )
    name_eje_x = forms.CharField(
        label='Nombre de Eje X',
        initial='Eje X',
        max_length=50,
        help_text='Etiqueta para el eje horizontal'
    )
    name_eje_y = forms.CharField(
        label='Nombre de Eje Y',
        initial='Eje Y',
        max_length=50,
        help_text='Etiqueta para el eje vertical'
    )    