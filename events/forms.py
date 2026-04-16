from django import forms


def build_registration_form(event, data=None, files=None):
    """
    Costruisce dinamicamente un Form Django dai RegistrationField dell'evento.
    Aggiunge sempre il campo _email in cima per la conferma.
    """
    field_dict = {}

    # Campo email sempre presente
    field_dict['reg_email'] = forms.EmailField(
        label='La tua email',
        help_text='Riceverai la conferma di iscrizione a questo indirizzo',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'es. mario.rossi@email.it'}),
    )

    for rf in event.fields.all():
        field_name = f'field_{rf.pk}'
        widget_attrs = {'class': 'form-control'}

        if rf.field_type == 'text':
            field = forms.CharField(
                max_length=500,
                widget=forms.TextInput(attrs=widget_attrs),
            )
        elif rf.field_type == 'email':
            field = forms.EmailField(
                widget=forms.EmailInput(attrs=widget_attrs),
            )
        elif rf.field_type == 'phone':
            field = forms.CharField(
                max_length=50,
                widget=forms.TextInput(attrs={**widget_attrs, 'type': 'tel'}),
            )
        elif rf.field_type == 'number':
            field = forms.DecimalField(
                widget=forms.NumberInput(attrs=widget_attrs),
            )
        elif rf.field_type == 'textarea':
            field = forms.CharField(
                widget=forms.Textarea(attrs={**widget_attrs, 'rows': 4}),
            )
        elif rf.field_type == 'select':
            options = rf.get_options_list()
            choices = [('', '— Seleziona —')] + [(o, o) for o in options]
            field = forms.ChoiceField(
                choices=choices,
                widget=forms.Select(attrs=widget_attrs),
            )
        elif rf.field_type == 'radio':
            options = rf.get_options_list()
            choices = [(o, o) for o in options]
            field = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            )
        elif rf.field_type == 'checkbox':
            field = forms.BooleanField(
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            )
        elif rf.field_type == 'file':
            field = forms.FileField(
                widget=forms.ClearableFileInput(attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
                }),
            )
        elif rf.field_type == 'date':
            field = forms.DateField(
                widget=forms.DateInput(attrs={**widget_attrs, 'type': 'date'}),
            )
        else:
            field = forms.CharField(widget=forms.TextInput(attrs=widget_attrs))

        field.label = rf.label
        field.help_text = rf.help_text
        field.required = rf.required
        field_dict[field_name] = field

    FormClass = type('RegistrationForm', (forms.BaseForm,), {'base_fields': field_dict})
    return FormClass(data=data, files=files)
