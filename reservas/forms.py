from django import forms
from .models import Espaco


class EspacoForm(forms.ModelForm):
    class Meta:
        model = Espaco
        fields = [
            'nome',
            'descricao',
            'capacidade',
            'valor_socio',
            'caucao',
            'horario_inicio',
            'horario_fim',
            'foto_capa',
            'churrasqueira',
            'cozinha',
            'freezer',
            'geladeira',
            'ar_condicionado',
            'wifi',
            'estacionamento',
            'banheiros',
            'regras',
            'status',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salão de Festas'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do espaço'
            }),
            'capacidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'valor_socio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'caucao': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'horario_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'horario_fim': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'foto_capa': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'regras': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Regras de utilização do espaço'
            }),
            'churrasqueira': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cozinha': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'freezer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'geladeira': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ar_condicionado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wifi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estacionamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'banheiros': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }