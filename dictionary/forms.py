from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Word, Category, Language, Tag

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма для создания пользователя"""
    email = forms.EmailField(required=False, help_text='Необязательно')
    first_name = forms.CharField(max_length=30, required=False, help_text='Необязательно')
    last_name = forms.CharField(max_length=30, required=False, help_text='Необязательно')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = ''
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label if field.label else ''
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user

class WordForm(forms.ModelForm):
    """Форма для создания/редактирования слов"""
    meaning = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Введите значение слова...'
        }),
        label='Значение',
        help_text='Поддерживает многострочный текст'
    )
    
    class Meta:
        model = Word
        fields = ['word', 'meaning', 'language', 'category', 'tags', 'status']
        widgets = {
            'word': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class WordTranslationForm(forms.Form):
    """Форма для перевода слов"""
    def __init__(self, languages, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for language in languages:
            self.fields[f'translation_word_{language.code}'] = forms.CharField(
                label=f'Перевод на {language.name}',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
            
            self.fields[f'translation_meaning_{language.code}'] = forms.CharField(
                label=f'Значение на {language.name}',
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': f'Введите значение на {language.name}'
                }),
                required=False
            )
            
            self.fields[f'note_{language.code}'] = forms.CharField(
                label=f'Примечание для {language.name}',
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                required=False
            ) 