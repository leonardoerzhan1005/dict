// Кастомные функции для TinyMCE

// Обработчик загрузки изображений
function image_upload_handler(blobInfo, success, failure, progress) {
    var xhr, formData;
    xhr = new XMLHttpRequest();
    xhr.withCredentials = false;
    xhr.open('POST', '/tinymce/upload/image/');
    
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    
    xhr.upload.onprogress = function (e) {
        progress(e.loaded / e.total * 100);
    };
    
    xhr.onload = function() {
        var json;
        
        if (xhr.status != 200) {
            failure('HTTP Error: ' + xhr.status);
            return;
        }
        
        json = JSON.parse(xhr.responseText);
        
        if (!json || typeof json.location != 'string') {
            failure('Invalid JSON: ' + xhr.responseText);
            return;
        }
        
        success(json.location);
    };
    
    xhr.onerror = function () {
        failure('Image upload failed due to a XHR Transport error');
    };
    
    formData = new FormData();
    formData.append('file', blobInfo.blob(), blobInfo.filename());
    
    xhr.send(formData);
}

// Обработчик выбора файлов
function file_picker_callback(callback, value, meta) {
    var input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain');
    
    input.onchange = function () {
        var file = this.files[0];
        var xhr = new XMLHttpRequest();
        var formData = new FormData();
        
        xhr.open('POST', '/tinymce/upload/file/');
        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
                callback(json.location, {title: file.name});
            } else {
                console.error('Upload failed');
            }
        };
        
        formData.append('file', file);
        xhr.send(formData);
    };
    
    input.click();
}

// Настройка редактора
function editor_setup(editor) {
    // Добавляем кастомные кнопки
    editor.ui.registry.addButton('customlink', {
        text: 'Ссылка',
        icon: 'link',
        onAction: function () {
            editor.windowManager.open({
                title: 'Вставить ссылку',
                body: {
                    type: 'panel',
                    items: [
                        {
                            type: 'input',
                            name: 'url',
                            label: 'URL'
                        },
                        {
                            type: 'input',
                            name: 'text',
                            label: 'Текст ссылки'
                        }
                    ]
                },
                buttons: [
                    {
                        type: 'submit',
                        text: 'Вставить'
                    }
                ],
                onSubmit: function (api) {
                    var data = api.getData();
                    editor.insertContent('<a href="' + data.url + '">' + data.text + '</a>');
                    api.close();
                }
            });
        }
    });
    
    // Добавляем кнопку для вставки таблицы
    editor.ui.registry.addButton('customtable', {
        text: 'Таблица',
        icon: 'table',
        onAction: function () {
            editor.windowManager.open({
                title: 'Вставить таблицу',
                body: {
                    type: 'panel',
                    items: [
                        {
                            type: 'input',
                            name: 'rows',
                            label: 'Количество строк',
                            value: '3'
                        },
                        {
                            type: 'input',
                            name: 'cols',
                            label: 'Количество столбцов',
                            value: '3'
                        }
                    ]
                },
                buttons: [
                    {
                        type: 'submit',
                        text: 'Вставить'
                    }
                ],
                onSubmit: function (api) {
                    var data = api.getData();
                    var rows = parseInt(data.rows);
                    var cols = parseInt(data.cols);
                    var table = '<table border="1" cellpadding="5" cellspacing="0">';
                    
                    for (var i = 0; i < rows; i++) {
                        table += '<tr>';
                        for (var j = 0; j < cols; j++) {
                            table += '<td>&nbsp;</td>';
                        }
                        table += '</tr>';
                    }
                    table += '</table>';
                    
                    editor.insertContent(table);
                    api.close();
                }
            });
        }
    });
}

// Инициализация редактора
function editor_init(editor) {
    // Добавляем обработчики событий
    editor.on('change', function() {
        console.log('Content changed');
    });
    
    editor.on('keyup', function(e) {
        if (e.keyCode === 13) { // Enter key
            console.log('Enter pressed');
        }
    });
    
    // Добавляем кастомные стили
    editor.dom.addStyle(
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }' +
        'table { border-collapse: collapse; width: 100%; }' +
        'table td, table th { border: 1px solid #ddd; padding: 8px; }' +
        'table th { background-color: #f2f2f2; }' +
        'blockquote { border-left: 4px solid #ccc; margin: 0; padding-left: 16px; }' +
        'code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }'
    );
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

// Добавляем кастомные стили для редактора
document.addEventListener('DOMContentLoaded', function() {
    var style = document.createElement('style');
    style.textContent = `
        .tox-tinymce {
            border-radius: 8px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        }
        .tox .tox-toolbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        .tox .tox-tbtn {
            color: white !important;
        }
        .tox .tox-tbtn:hover {
            background-color: rgba(255,255,255,0.2) !important;
        }
    `;
    document.head.appendChild(style);
}); 