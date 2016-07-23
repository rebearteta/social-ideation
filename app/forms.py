from django import forms
import choices

class SignInForm (forms.Form):
   name = forms.CharField(label = "Nombre Completo", max_length=100)
   email = forms.EmailField(label = "E-mail", widget=forms.TextInput(attrs={ 'required': 'true' }))
   age = forms.ChoiceField(choices=choices.GRUPOS_ETARIOS, label = "Edad")
   sex = forms.ChoiceField(choices=choices.SEXOS, label = "Sexo")
   city = forms.ChoiceField(choices=choices.CIUDADES, label = "Ciudad de Residencia")
   
