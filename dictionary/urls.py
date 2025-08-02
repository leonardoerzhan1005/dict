from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Главная страница с поиском
    path('', views.home, name='home'),
    
    # Детальная страница слова
    path('word/<int:word_id>/', views.word_detail, name='word_detail'),
    
    # Аутентификация
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('profile/', views.user_profile, name='profile'),
    
    # Управление переводами
    path('translations/', views.translation_dashboard, name='translation_dashboard'),
    path('translations/category/<int:category_id>/', views.category_translations_edit, name='category_translations_edit'),
    path('translations/tag/<int:tag_id>/', views.tag_translations_edit, name='tag_translations_edit'),
    path('translations/interface/', views.interface_translations_edit, name='interface_translations_edit'),
    path('translations/add-missing/', views.add_missing_translations, name='add_missing_translations'),
    path('translations/bulk-add/', views.bulk_add_missing_translations, name='bulk_add_missing_translations'),
    path('translations/progress/', views.translation_progress, name='translation_progress'),
    
    # Управление переводами слов
    path('word-translations/', views.word_translations_dashboard, name='word_translations_dashboard'),
    path('word-translations/edit/<int:word_id>/', views.word_translation_edit, name='word_translation_edit'),
    path('word-translations/bulk/', views.bulk_word_translation, name='bulk_word_translation'),
    path('translation-search/', views.translation_search, name='translation_search'),
    
    # Создание и редактирование слов
    path('word/create/', views.word_create, name='word_create'),
    path('word/edit/<int:word_id>/', views.word_edit, name='word_edit'),
    
    # Мультиперевод
    path('multi-translate/<int:word_id>/', views.multi_translate_word, name='multi_translate_word'),
    path('bulk-multi-translate/', views.bulk_multi_translate, name='bulk_multi_translate'),
    path('quick-translate/', views.quick_translate, name='quick_translate'),
    path('quick-translate/<int:term_id>/', views.quick_translate_detail, name='quick_translate_detail'),
    path('auto-fill-translations/', views.auto_fill_translations, name='auto_fill_translations'),
] 

