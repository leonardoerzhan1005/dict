from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from tinymce.widgets import TinyMCE
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
        widget=TinyMCE(
            attrs={'cols': 80, 'rows': 20},
            mce_attrs={
                'height': 300,
                'width': '100%',
                'plugins': 'save link image imagetools table paste lists advlist wordcount charmap nonbreaking anchor pagebreak insertdatetime media directionality emoticons template paste textpattern imagetools codesample',
                'toolbar1': 'save | formatselect | bold italic underline | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image media | forecolor backcolor emoticons',
                'toolbar2': 'table | charmap | pagebreak | codesample | ltr rtl | spellchecker | advlist | autolink | lists charmap | print preview | anchor',
                'contextmenu': 'formats | link image',
                'menubar': True,
                'statusbar': True,
                'language': 'ru',
                'relative_urls': False,
                'remove_script_host': False,
                'convert_urls': False,
                'entity_encoding': 'raw',
                'verify_html': False,
                'browser_spellcheck': True,
                'paste_data_images': True,
                'images_upload_url': '/admin/tinymce/upload/',
                'images_upload_credentials': True,
                'automatic_uploads': True,
                'file_picker_types': 'image',
                'images_reuse_filename': True,
                'images_upload_base_path': '/media/',
            }
        ),
        label='Значение',
        help_text='Используйте редактор для форматирования текста'
    )
    
    class Meta:
        model = Word
        fields = ['word', 'meaning', 'language', 'category', 'tags', 'status', 'pronunciation', 'difficulty']
        widgets = {
            'word': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'pronunciation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'МФА транскрипция'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
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