from django import forms


class ContattoForm(forms.Form):
    nome = forms.CharField(max_length=100, label='Nome')
    email = forms.EmailField(label='Email')
    oggetto = forms.CharField(max_length=200, label='Oggetto')
    messaggio = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}), label='Messaggio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
