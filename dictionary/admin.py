from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.urls import reverse
from tinymce.widgets import TinyMCE
from .models import (
    Language, CustomUser, Category, CategoryTranslation, Tag, TagTranslation,
    Word, Translation, Example, Favourite, SearchHistory, WordLike,
    WordChangeLog, WordHistory, InterfaceTranslation
)

# Добавляем ссылку на дашборд переводов в админку
class TranslationDashboardAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['translation_dashboard_url'] = reverse('dictionary:translation_dashboard')
        return super().changelist_view(request, extra_context)

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
    ordering = ['code']

class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 0
    fields = ['language', 'name', 'description']
    ordering = ['language__code']

@admin.register(Category)
class CategoryAdmin(TranslationDashboardAdmin):
    list_display = ['code', 'get_translations_summary', 'get_missing_translations']
    search_fields = ['code']
    inlines = [CategoryTranslationInline]
    actions = ['add_missing_translations']
    
    def get_translations_summary(self, obj):
        translations = obj.translations.all()
        if not translations:
            return format_html('<span style="color: red;">Нет переводов</span>')
        
        summary = []
        for t in translations.order_by('language__code'):
            summary.append(f"{t.language.code}: {t.name}")
        
        return format_html('<br>'.join(summary))
    get_translations_summary.short_description = 'Переводы'
    
    def get_missing_translations(self, obj):
        all_languages = Language.objects.all()
        existing_languages = set(obj.translations.values_list('language__code', flat=True))
        missing = [lang.code for lang in all_languages if lang.code not in existing_languages]
        
        if missing:
            return format_html('<span style="color: orange;">Отсутствуют: {}</span>', ', '.join(missing))
        return format_html('<span style="color: green;">Все языки</span>')
    get_missing_translations.short_description = 'Статус переводов'
    
    def add_missing_translations(self, request, queryset):
        all_languages = Language.objects.all()
        created_count = 0
        
        for category in queryset:
            existing_languages = set(category.translations.values_list('language__code', flat=True))
            missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
            
            for lang in missing_languages:
                CategoryTranslation.objects.create(
                    category=category,
                    language=lang,
                    name=f"[{lang.code}] {category.code}",
                    description=""
                )
                created_count += 1
        
        self.message_user(request, f'Создано {created_count} недостающих переводов')
    add_missing_translations.short_description = 'Добавить недостающие переводы'

class TagTranslationInline(admin.TabularInline):
    model = TagTranslation
    extra = 0
    fields = ['language', 'name']
    ordering = ['language__code']

@admin.register(Tag)
class TagAdmin(TranslationDashboardAdmin):
    list_display = ['code', 'get_translations_summary', 'get_missing_translations']
    search_fields = ['code']
    inlines = [TagTranslationInline]
    actions = ['add_missing_translations']
    
    def get_translations_summary(self, obj):
        translations = obj.translations.all()
        if not translations:
            return format_html('<span style="color: red;">Нет переводов</span>')
        
        summary = []
        for t in translations.order_by('language__code'):
            summary.append(f"{t.language.code}: {t.name}")
        
        return format_html('<br>'.join(summary))
    get_translations_summary.short_description = 'Переводы'
    
    def get_missing_translations(self, obj):
        all_languages = Language.objects.all()
        existing_languages = set(obj.translations.values_list('language__code', flat=True))
        missing = [lang.code for lang in all_languages if lang.code not in existing_languages]
        
        if missing:
            return format_html('<span style="color: orange;">Отсутствуют: {}</span>', ', '.join(missing))
        return format_html('<span style="color: green;">Все языки</span>')
    get_missing_translations.short_description = 'Статус переводов'
    
    def add_missing_translations(self, request, queryset):
        all_languages = Language.objects.all()
        created_count = 0
        
        for tag in queryset:
            existing_languages = set(tag.translations.values_list('language__code', flat=True))
            missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
            
            for lang in missing_languages:
                TagTranslation.objects.create(
                    tag=tag,
                    language=lang,
                    name=f"[{lang.code}] {tag.code}"
                )
                created_count += 1
        
        self.message_user(request, f'Создано {created_count} недостающих переводов')
    add_missing_translations.short_description = 'Добавить недостающие переводы'

class TranslationInline(admin.TabularInline):
    model = Translation
    fk_name = 'from_word'
    extra = 1
    verbose_name = 'Перевод'
    verbose_name_plural = 'Переводы'
    fields = ['to_word', 'note', 'order', 'status']

class ExampleInline(admin.TabularInline):
    model = Example
    extra = 1

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['word', 'language', 'category', 'status', 'created_at']
    list_filter = ['language', 'category', 'status', 'created_at', 'difficulty']
    search_fields = ['word', 'meaning']
    inlines = [TranslationInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['meaning'].widget = TinyMCE(
            attrs={'cols': 80, 'rows': 20},
            mce_attrs={
                'height': 500,
                'width': '100%',
                'plugins': 'save link image table paste lists advlist wordcount charmap nonbreaking anchor pagebreak insertdatetime media directionality emoticons template paste textpattern codesample advlist autolink lists link image charmap preview anchor pagebreak insertdatetime media table code help wordcount',
                'toolbar1': 'save | formatselect | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image media table | forecolor backcolor emoticons | fontselect fontsizeselect',
                'toolbar2': 'table | charmap | pagebreak | codesample | ltr rtl | spellchecker | advlist | autolink | lists charmap | print preview | anchor | insertdatetime | media | help',
                'toolbar3': 'undo redo | cut copy paste | searchreplace | visualblocks visualchars | fullscreen | insertfile image media template link anchor | ltr rtl',
                'contextmenu': 'formats | link image table',
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
                'images_upload_url': '/tinymce/upload/image/',
                'file_picker_types': 'image file',
                'images_reuse_filename': True,
                'images_upload_base_path': '/media/',
                'automatic_uploads': True,
                'images_upload_credentials': True,
                'paste_data_images': True,
                'file_picker_callback': 'file_picker_callback',
                'setup': '''
                    function(editor) {
                        console.log('TinyMCE инициализирован');
                        
                        // Подавляем предупреждения о политике разрешений
                        if (window.console && window.console.warn) {
                            var originalWarn = console.warn;
                            console.warn = function() {
                                if (arguments[0] && typeof arguments[0] === 'string' && 
                                    arguments[0].includes('Permissions policy violation')) {
                                    return;
                                }
                                return originalWarn.apply(console, arguments);
                            };
                        }
                        
                        // Функция для получения CSRF токена
                        function getCookie(name) {
                            var cookieValue = null;
                            if (document.cookie && document.cookie !== '') {
                                var cookies = document.cookie.split(';');
                                for (var i = 0; i < cookies.length; i++) {
                                    var cookie = cookies[i].trim();
                                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                        break;
                                    }
                                }
                            }
                            return cookieValue;
                        }
                        
                        // Добавляем обработчик для отладки
                        editor.on('change', function() {
                            console.log('Контент изменен');
                        });
                        
                        // Добавляем обработчик для загрузки изображений
                        editor.on('BeforeSetContent', function(e) {
                            console.log('Устанавливаем контент:', e.content);
                        });
                        
                        editor.on('SetContent', function(e) {
                            console.log('Контент установлен');
                        });
                    }
                ''',

                'content_style': 'body { font-family: "Charter", "Georgia", "Times New Roman", serif; font-size: 16px; line-height: 1.7; color: #1a1a1a; } @import url("/static/css/tinymce-content.css");',
                'browser_spellcheck': True,
                'paste_data_images': True,
                'automatic_uploads': True,
                'images_upload_credentials': True,
                'file_picker_types': 'image file',
                'images_reuse_filename': True,
                'images_upload_base_path': '/media/',
                'verify_html': False,
                'entity_encoding': 'raw',
                'relative_urls': False,
                'remove_script_host': False,
                'convert_urls': False,
                'extended_valid_elements': 'img[src|alt|title|width|height|style],a[href|target|title],table[width|height|border|cellpadding|cellspacing|style],tr[style],td[width|height|style|colspan|rowspan],th[width|height|style|colspan|rowspan]',
                'custom_colors': 'FF0000,00FF00,0000FF,FFFF00,FF00FF,00FFFF,000000,FFFFFF',
                'color_map': [
                    '000000', 'Black',
                    '993300', 'Burnt orange',
                    '333300', 'Dark olive',
                    '003300', 'Dark green',
                    '003366', 'Dark azure',
                    '000080', 'Navy Blue',
                    '333399', 'Indigo',
                    '333333', 'Very dark gray',
                    '800000', 'Maroon',
                    'FF6600', 'Orange',
                    '808000', 'Olive',
                    '008000', 'Green',
                    '008080', 'Teal',
                    '0000FF', 'Blue',
                    '666699', 'Grayish blue',
                    '808080', 'Gray',
                    'FF0000', 'Red',
                    'FF9900', 'Amber',
                    '99CC00', 'Yellow green',
                    '339966', 'Sea green',
                    '33CCCC', 'Turquoise',
                    '3366FF', 'Royal blue',
                    '800080', 'Purple',
                    '999999', 'Medium gray',
                    'FF00FF', 'Magenta',
                    'FFCC00', 'Gold',
                    'FFFF00', 'Yellow',
                    '00FF00', 'Lime',
                    '00FFFF', 'Aqua',
                    '00CCFF', 'Sky blue',
                    '993366', 'Red violet',
                    'FFFFFF', 'White',
                    'FF99CC', 'Pink',
                    'FFCC99', 'Peach',
                    'FFFF99', 'Light yellow',
                    'CCFFCC', 'Pale green',
                    'CCFFFF', 'Pale cyan',
                    '99CCFF', 'Light sky blue',
                    'CC99FF', 'Plum'
                ],
            }
        )
        return form
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'meaning', 'language', 'category', 'tags')
        }),
        ('Дополнительная информация', {
            'fields': ('pronunciation', 'difficulty')
        }),
        ('Статус', {
            'fields': ('status', 'is_deleted')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ['from_word', 'to_word', 'status', 'order', 'note']
    list_filter = ['status', 'from_word__language', 'to_word__language']
    search_fields = ['from_word__word', 'to_word__word', 'note']
    ordering = ['from_word', 'order']

@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['word', 'text_preview', 'author', 'created_at']
    list_filter = ['created_at', 'word__language']
    search_fields = ['text', 'word__word']
    readonly_fields = ['created_at']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'

@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'word', 'added_at']
    list_filter = ['added_at', 'word__language']
    search_fields = ['user__username', 'word__word']
    readonly_fields = ['added_at']

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'word', 'searched_at']
    list_filter = ['searched_at']
    search_fields = ['user__username', 'word']
    readonly_fields = ['searched_at']
    ordering = ['-searched_at']

@admin.register(WordLike)
class WordLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'word', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at', 'word__language']
    search_fields = ['user__username', 'word__word']
    readonly_fields = ['created_at']

@admin.register(WordChangeLog)
class WordChangeLogAdmin(admin.ModelAdmin):
    list_display = ['word', 'user', 'action', 'change_type', 'timestamp']
    list_filter = ['action', 'change_type', 'timestamp', 'word__language']
    search_fields = ['word__word', 'user__username', 'comment']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

@admin.register(WordHistory)
class WordHistoryAdmin(admin.ModelAdmin):
    list_display = ['word', 'changed_by', 'changed_at']
    list_filter = ['changed_at', 'word__language']
    search_fields = ['word__word', 'changed_by__username']
    readonly_fields = ['changed_at', 'data']
    ordering = ['-changed_at']

@admin.register(InterfaceTranslation)
class InterfaceTranslationAdmin(admin.ModelAdmin):
    list_display = ['language', 'key', 'value_preview', 'get_status']
    list_filter = ['language']
    search_fields = ['key', 'value']
    ordering = ['language', 'key']
    actions = ['add_missing_keys']
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Значение'
    
    def get_status(self, obj):
        if not obj.value or obj.value.strip() == '':
            return format_html('<span style="color: red;">Пусто</span>')
        elif obj.value.startswith('[') and obj.value.endswith(']'):
            return format_html('<span style="color: orange;">Заглушка</span>')
        else:
            return format_html('<span style="color: green;">Переведено</span>')
    get_status.short_description = 'Статус'
    
    def add_missing_keys(self, request, queryset):
        # Получаем все уникальные ключи
        all_keys = set(InterfaceTranslation.objects.values_list('key', flat=True))
        all_languages = Language.objects.all()
        created_count = 0
        
        for key in all_keys:
            existing_languages = set(InterfaceTranslation.objects.filter(key=key).values_list('language__code', flat=True))
            missing_languages = [lang for lang in all_languages if lang.code not in existing_languages]
            
            for lang in missing_languages:
                InterfaceTranslation.objects.create(
                    language=lang,
                    key=key,
                    value=f"[{lang.code}] {key}"
                )
                created_count += 1
        
        self.message_user(request, f'Создано {created_count} недостающих переводов интерфейса')
    add_missing_keys.short_description = 'Добавить недостающие переводы интерфейса'

# Расширенная админка для CustomUser
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'preferred_language', 'is_moderator', 'is_verified', 'is_staff', 'is_active']
    list_filter = ['is_moderator', 'is_verified', 'is_staff', 'is_active', 'preferred_language', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    

    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('preferred_language', 'bio', 'avatar', 'is_moderator', 'is_verified', 'registration_source')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('preferred_language', 'bio', 'avatar', 'is_moderator', 'is_verified', 'registration_source')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# Настройки админки
admin.site.site_header = 'Админка многоязычного словаря'
admin.site.site_title = 'Словарь'
admin.site.index_title = 'Управление словарём'

# Добавляем ссылку на дашборд переводов в админку
admin.site.index_template = 'admin/custom_index.html'
