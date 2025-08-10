from django.urls import path
from . import views
from . import api_views

app_name = 'dictionary'

urlpatterns = [
    # Главная страница с поиском
    path('', views.home, name='home'),
    
    # Создание и редактирование слов (должны идти перед word/<slug:slug>/)
    path('word/create/', views.word_create, name='word_create'),
    path('word/edit/<slug:slug>/', views.word_edit, name='word_edit'),
    
    # Детальная страница слова (используем slug)
    path('word/<slug:slug>/', views.word_detail, name='word_detail'),
    
    # Аутентификация
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('profile/', views.user_profile, name='profile'),
    
    # TinyMCE загрузка файлов
    path('tinymce/upload/file/', views.tinymce_upload_file, name='tinymce_upload_file'),
    path('tinymce/upload/image/', views.tinymce_upload_image, name='tinymce_upload_image'),
    
    # API endpoints
    path('api/check-translations/', views.check_translations_api, name='check_translations_api'),
    path('api/create-category/', views.create_category_api, name='create_category_api'),
    path('api/create-tag/', views.create_tag_api, name='create_tag_api'),
    path('api/change-word-status/<slug:slug>/', views.change_word_status, name='change_word_status'),
    path('api/get-category/<int:category_id>/', api_views.get_category_api, name='get_category_api'),
    path('api/update-category/<int:category_id>/', api_views.update_category_api, name='update_category_api'),
    path('api/delete-category/<int:category_id>/', api_views.delete_category_api, name='delete_category_api'),
    path('api/get-tags/', api_views.get_tags_api, name='get_tags_api'),
    path('api/update-tag/<int:tag_id>/', api_views.update_tag_api, name='update_tag_api'),
    path('api/delete-tag/<int:tag_id>/', api_views.delete_tag_api, name='delete_tag_api'),
    
    # Управление переводами
    path('translations/', views.translation_dashboard, name='translation_dashboard'),
    path('translations/category/<slug:slug>/', views.category_translations_edit, name='category_translations_edit'),
    path('translations/tag/<slug:slug>/', views.tag_translations_edit, name='tag_translations_edit'),
    path('translations/interface/', views.interface_translations_edit, name='interface_translations_edit'),
    path('translations/add-missing/', views.add_missing_translations, name='add_missing_translations'),
    path('translations/bulk-add/', views.bulk_add_missing_translations, name='bulk_add_missing_translations'),
    path('translations/progress/', views.translation_progress, name='translation_progress'),
    
    # Управление переводами слов
    path('word-translations/', views.word_translations_dashboard, name='word_translations_dashboard'),
    path('word-translations/edit/<slug:slug>/', views.word_translation_edit, name='word_translation_edit'),
    # Альтернативный URL для удобства
    path('word/translations/edit/<slug:slug>/', views.word_translation_edit, name='word_translations_edit_alt'),
    path('word-translations/bulk/', views.bulk_word_translation, name='bulk_word_translation'),
    path('translation-search/', views.translation_search, name='translation_search'),
    
    # Тестовый endpoint для проверки сохранения переводов
    path('test-translation/<slug:slug>/', views.test_translation_save, name='test_translation_save'),
    path('test-translation-page/<slug:slug>/', views.test_translation_page, name='test_translation_page'),
    
    # Мультиперевод
    path('multi-translate/<slug:slug>/', views.multi_translate_word, name='multi_translate_word'),
    path('bulk-multi-translate/', views.bulk_multi_translate, name='bulk_multi_translate'),
    path('quick-translate/', views.quick_translate, name='quick_translate'),
    path('quick-translate/<slug:slug>/', views.quick_translate_detail, name='quick_translate_detail'),
    path('auto-fill-translations/', views.auto_fill_translations, name='auto_fill_translations'),
] 

