from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.urls import reverse
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
    list_filter = ['language', 'category', 'status', 'created_at']
    search_fields = ['word', 'meaning']
    inlines = [TranslationInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'meaning', 'language', 'category', 'tags')
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
