from django import forms
from registro.models import ColetaFaces, Funcionario

TAILWIND_CLASSES = (
            "w-full p-3 border border-gray-300 rounded-lg "
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 "
            "transition duration-150"
        )

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['foto','nome', 'cpf']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            current_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{current_classes} {TAILWIND_CLASSES}"
  
            
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result   

class ColetaFacesForm(forms.ModelForm):
    
    foto = MultipleFileField()
    
    class Meta:
        model = ColetaFaces
        fields = ['foto']
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            current_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{current_classes} {TAILWIND_CLASSES}"
            field.widget.attrs['multiple'] = True
            