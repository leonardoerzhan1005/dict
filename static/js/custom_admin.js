// Улучшения для Django Admin

document.addEventListener('DOMContentLoaded', function() {
    
    // Добавляем статусные классы к строкам таблицы
    function addStatusClasses() {
        const rows = document.querySelectorAll('.results tbody tr');
        rows.forEach(row => {
            const statusCell = row.querySelector('td:nth-child(4)'); // Предполагаем, что статус в 4-й колонке
            if (statusCell) {
                const status = statusCell.textContent.trim().toLowerCase();
                if (status.includes('на проверке')) {
                    row.classList.add('status-pending');
                } else if (status.includes('опубликовано')) {
                    row.classList.add('status-approved');
                } else if (status.includes('отклонено')) {
                    row.classList.add('status-rejected');
                }
            }
        });
    }
    
    // Улучшенные уведомления
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Закрытие по клику
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        });
    }
    
    // Улучшенная валидация форм
    function enhanceFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const requiredFields = form.querySelectorAll('[required]');
                let hasErrors = false;
                
                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.style.borderColor = '#e74c3c';
                        hasErrors = true;
                    } else {
                        field.style.borderColor = '';
                    }
                });
                
                if (hasErrors) {
                    e.preventDefault();
                    showNotification('Пожалуйста, заполните все обязательные поля', 'error');
                }
            });
        });
    }
    
    // Быстрые действия
    function addQuickActions() {
        const actionButtons = document.querySelectorAll('.object-tools a');
        actionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (this.textContent.includes('Добавить')) {
                    showNotification('Создание нового элемента...', 'info');
                }
            });
        });
    }
    
    // Улучшенный поиск
    function enhanceSearch() {
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.placeholder = 'Поиск по словам, переводам, категориям...';
            searchInput.style.cssText = `
                padding: 12px 15px;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                font-size: 16px;
                transition: border-color 0.3s ease;
            `;
            
            searchInput.addEventListener('focus', function() {
                this.style.borderColor = '#3498db';
            });
            
            searchInput.addEventListener('blur', function() {
                this.style.borderColor = '#ecf0f1';
            });
        }
    }
    
    // Подсветка изменений
    function highlightChanges() {
        const formFields = document.querySelectorAll('input, textarea, select');
        formFields.forEach(field => {
            const originalValue = field.value;
            field.addEventListener('change', function() {
                if (this.value !== originalValue) {
                    this.style.backgroundColor = '#fff3cd';
                    this.style.borderColor = '#ffc107';
                } else {
                    this.style.backgroundColor = '';
                    this.style.borderColor = '';
                }
            });
        });
    }
    
    // Инициализация всех улучшений
    function init() {
        addStatusClasses();
        enhanceFormValidation();
        addQuickActions();
        enhanceSearch();
        highlightChanges();
        
        // Добавляем CSS анимации
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Запускаем инициализацию
    init();
    
    // Глобальные функции для использования в других скриптах
    window.adminUtils = {
        showNotification,
        addStatusClasses,
        enhanceFormValidation
    };
}); 