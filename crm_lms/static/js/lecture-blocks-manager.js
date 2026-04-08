/**
 * Улучшенный менеджер блоков лекций
 * Поддерживает Drag & Drop, контекстные меню, анимации
 */

// Защита от повторного объявления
if (typeof LectureBlocksManager === 'undefined') {

class LectureBlocksManager {
    constructor(options = {}) {
        this.container = options.container || '#lecture-content';
        this.blocksContainer = options.blocksContainer || '#lecture-content';
        this.lectureId = options.lectureId || null;
        this.draggedElement = null;
        this.dragOverElement = null;
        this.contextMenuTarget = null;
        
        this.init();
    }
    
    init() {
        this.setupDragAndDrop();
        this.setupContextMenu();
        this.setupBlockActions();
        this.setupKeyboardShortcuts();
        this.setupAutoSave();
    }
    
    /**
     * Настройка Drag & Drop
     */
    setupDragAndDrop() {
        const container = document.querySelector(this.container);
        if (!container) return;
        
        // Обработчики для перетаскивания
        container.addEventListener('dragstart', this.handleDragStart.bind(this));
        container.addEventListener('dragover', this.handleDragOver.bind(this));
        container.addEventListener('drop', this.handleDrop.bind(this));
        container.addEventListener('dragend', this.handleDragEnd.bind(this));
        container.addEventListener('dragenter', this.handleDragEnter.bind(this));
        container.addEventListener('dragleave', this.handleDragLeave.bind(this));
    }
    
    handleDragStart(e) {
        if (!e.target.classList.contains('lecture-block')) return;
        
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.innerHTML);
        
        // Задержка для визуального эффекта
        setTimeout(() => {
            e.target.style.opacity = '0.5';
        }, 0);
    }
    
    handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    handleDragEnter(e) {
        const block = e.target.closest('.lecture-block');
        if (block && block !== this.draggedElement) {
            block.classList.add('drag-over');
            this.dragOverElement = block;
        }
    }
    
    handleDragLeave(e) {
        const block = e.target.closest('.lecture-block');
        if (block) {
            block.classList.remove('drag-over');
        }
    }
    
    handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        if (this.draggedElement && this.dragOverElement && this.draggedElement !== this.dragOverElement) {
            // Определяем куда вставлять (до или после)
            const rect = this.dragOverElement.getBoundingClientRect();
            const midpoint = rect.top + rect.height / 2;
            
            if (e.clientY < midpoint) {
                // Вставляем перед элементом
                this.dragOverElement.parentNode.insertBefore(this.draggedElement, this.dragOverElement);
            } else {
                // Вставляем после элемента
                this.dragOverElement.parentNode.insertBefore(this.draggedElement, this.dragOverElement.nextSibling);
            }
            
            // Сохраняем новый порядок
            this.saveBlockOrder();
            
            // Анимация
            this.animateBlockInsertion(this.draggedElement);
        }
        
        return false;
    }
    
    handleDragEnd(e) {
        // Убираем все классы drag-over
        document.querySelectorAll('.lecture-block').forEach(block => {
            block.classList.remove('drag-over', 'dragging');
            block.style.opacity = '';
        });
        
        this.draggedElement = null;
        this.dragOverElement = null;
    }
    
    /**
     * Настройка контекстного меню
     */
    setupContextMenu() {
        // Закрытие меню при клике вне его
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.block-context-menu')) {
                this.hideContextMenu();
            }
        });
        
        // Обработчики для блоков
        document.addEventListener('contextmenu', (e) => {
            const block = e.target.closest('.lecture-block');
            if (block) {
                e.preventDefault();
                this.showContextMenu(e, block);
            }
        });
    }
    
    showContextMenu(e, block) {
        this.hideContextMenu();
        this.contextMenuTarget = block;
        
        const menu = this.createContextMenu();
        document.body.appendChild(menu);
        
        // Позиционирование меню
        const x = e.pageX;
        const y = e.pageY;
        
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        menu.classList.add('show');
        
        // Проверка выхода за границы экрана
        const rect = menu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            menu.style.left = (x - rect.width) + 'px';
        }
        if (rect.bottom > window.innerHeight) {
            menu.style.top = (y - rect.height) + 'px';
        }
    }
    
    hideContextMenu() {
        const existingMenu = document.querySelector('.block-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
    }
    
    createContextMenu() {
        const menu = document.createElement('div');
        menu.className = 'block-context-menu';
        
        const actions = [
            { icon: 'fa fa-edit', text: 'Редактировать', action: 'edit', class: '' },
            { icon: 'fa fa-copy', text: 'Дублировать', action: 'duplicate', class: '' },
            { icon: 'fa fa-arrow-up', text: 'Переместить вверх', action: 'move-up', class: '' },
            { icon: 'fa fa-arrow-down', text: 'Переместить вниз', action: 'move-down', class: '' },
            { icon: 'fa fa-trash', text: 'Удалить', action: 'delete', class: 'danger' }
        ];
        
        actions.forEach(action => {
            const link = document.createElement('a');
            link.href = '#';
            link.innerHTML = `<i class="${action.icon}"></i> ${action.text}`;
            link.className = action.class;
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleContextAction(action.action);
                this.hideContextMenu();
            });
            menu.appendChild(link);
        });
        
        return menu;
    }
    
    handleContextAction(action) {
        if (!this.contextMenuTarget) return;
        
        switch (action) {
            case 'edit':
                this.editBlock(this.contextMenuTarget);
                break;
            case 'duplicate':
                this.duplicateBlock(this.contextMenuTarget);
                break;
            case 'move-up':
                this.moveBlock(this.contextMenuTarget, 'up');
                break;
            case 'move-down':
                this.moveBlock(this.contextMenuTarget, 'down');
                break;
            case 'delete':
                this.deleteBlock(this.contextMenuTarget);
                break;
        }
    }
    
    /**
     * Настройка действий с блоками
     */
    setupBlockActions() {
        // Делегирование событий для кнопок редактирования/удаления
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-block')) {
                e.preventDefault();
                const block = e.target.closest('.lecture-block');
                this.deleteBlock(block);
            }
            
            if (e.target.classList.contains('edit-block') || e.target.closest('.edit-block')) {
                e.preventDefault();
                const block = e.target.closest('.lecture-block');
                this.editBlock(block);
            }
        });
    }
    
    /**
     * Редактирование блока
     */
    editBlock(block) {
        const blockId = block.dataset.blockId || block.id;
        if (!blockId) return;
        
        // Показываем индикатор загрузки
        this.showBlockLoading(block, true);
        
        // Загружаем форму редактирования через AJAX
        fetch(`/lms/mentor/lectures/block-${blockId}/edit/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            this.showEditModal(html, block);
        })
        .catch(error => {
            console.error('Error loading edit form:', error);
            this.showBlockLoading(block, false);
        });
    }
    
    showEditModal(html, block) {
        // Создаем модальное окно
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Редактировать блок</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${html}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Обработчик сохранения
        const form = modal.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveBlockEdit(form, block, bsModal);
            });
        }
        
        // Удаление модального окна после закрытия
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
    
    saveBlockEdit(form, block, modal) {
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем блок
                this.updateBlockContent(block, data.html);
                modal.hide();
                this.showNotification('Блок успешно обновлен', 'success');
            } else {
                this.showNotification('Ошибка при сохранении блока', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving block:', error);
            this.showNotification('Ошибка при сохранении блока', 'error');
        });
    }
    
    /**
     * Дублирование блока
     */
    duplicateBlock(block) {
        const blockId = block.dataset.blockId || block.id;
        if (!blockId) return;
        
        this.showBlockLoading(block, true);
        
        fetch(`/lms/mentor/lectures/block-${blockId}/duplicate/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Добавляем новый блок после текущего
                const newBlock = this.createBlockFromHTML(data.html);
                block.parentNode.insertBefore(newBlock, block.nextSibling);
                
                // Анимация
                newBlock.classList.add('new-block');
                setTimeout(() => newBlock.classList.remove('new-block'), 400);
                
                this.showNotification('Блок успешно дублирован', 'success');
            } else {
                this.showNotification('Ошибка при дублировании блока', 'error');
            }
            this.showBlockLoading(block, false);
        })
        .catch(error => {
            console.error('Error duplicating block:', error);
            this.showNotification('Ошибка при дублировании блока', 'error');
            this.showBlockLoading(block, false);
        });
    }
    
    /**
     * Перемещение блока
     */
    moveBlock(block, direction) {
        const sibling = direction === 'up' ? block.previousElementSibling : block.nextElementSibling;
        if (!sibling || !sibling.classList.contains('lecture-block')) return;
        
        if (direction === 'up') {
            sibling.parentNode.insertBefore(block, sibling);
        } else {
            block.parentNode.insertBefore(sibling, block);
        }
        
        // Анимация
        this.animateBlockInsertion(block);
        this.saveBlockOrder();
    }
    
    /**
     * Удаление блока
     */
    deleteBlock(block) {
        if (!confirm('Вы уверены, что хотите удалить этот блок?')) return;
        
        const blockId = block.dataset.blockId || block.id;
        if (!blockId) return;
        
        block.classList.add('removing');
        
        setTimeout(() => {
            fetch(`/lms/mentor/lectures/block-${blockId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    block.remove();
                    this.showNotification('Блок успешно удален', 'success');
                } else {
                    block.classList.remove('removing');
                    this.showNotification('Ошибка при удалении блока', 'error');
                }
            })
            .catch(error => {
                console.error('Error deleting block:', error);
                block.classList.remove('removing');
                this.showNotification('Ошибка при удалении блока', 'error');
            });
        }, 300);
    }
    
    /**
     * Сохранение порядка блоков
     */
    saveBlockOrder() {
        const blocks = document.querySelectorAll(`${this.container} .lecture-block`);
        const order = Array.from(blocks).map(block => block.dataset.blockId || block.id);
        
        fetch('/lms/mentor/lectures/reorder-blocks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ order: order })
        })
        .catch(error => {
            console.error('Error saving block order:', error);
        });
    }
    
    /**
     * Горячие клавиши
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter для сохранения
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const activeElement = document.activeElement;
                if (activeElement && activeElement.form) {
                    activeElement.form.dispatchEvent(new Event('submit'));
                }
            }
            
            // Escape для закрытия модальных окон
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    bootstrap.Modal.getInstance(modal)?.hide();
                }
                this.hideContextMenu();
            }
        });
    }
    
    /**
     * Автосохранение
     */
    setupAutoSave() {
        let saveTimeout;
        
        document.addEventListener('input', (e) => {
            if (e.target.closest('.modal')) {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    const form = e.target.closest('form');
                    if (form && form.dataset.autoSave !== 'false') {
                        this.autoSave(form);
                    }
                }, 2000);
            }
        });
    }
    
    autoSave(form) {
        const formData = new FormData(form);
        
        fetch(form.action + '?auto_save=1', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAutoSaveIndicator();
            }
        })
        .catch(error => {
            console.error('Auto save error:', error);
        });
    }
    
    /**
     * Вспомогательные методы
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }
    
    showBlockLoading(block, show) {
        const loader = block.querySelector('.block-loader') || this.createBlockLoader(block);
        loader.style.display = show ? 'block' : 'none';
    }
    
    createBlockLoader(block) {
        const loader = document.createElement('div');
        loader.className = 'block-loader';
        loader.innerHTML = '<div class="spinner-border spinner-border-sm"></div>';
        loader.style.cssText = 'position: absolute; top: 10px; right: 10px; z-index: 10;';
        block.appendChild(loader);
        return loader;
    }
    
    updateBlockContent(block, html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newContent = temp.firstElementChild;
        
        if (newContent) {
            block.replaceWith(newContent);
        }
    }
    
    createBlockFromHTML(html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        return temp.firstElementChild;
    }
    
    animateBlockInsertion(block) {
        block.classList.add('new-block');
        setTimeout(() => block.classList.remove('new-block'), 400);
    }
    
    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматическое скрытие
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    showAutoSaveIndicator() {
        const indicator = document.querySelector('.auto-save-indicator') || this.createAutoSaveIndicator();
        indicator.classList.add('show');
        
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }
    
    createAutoSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator';
        indicator.innerHTML = '<i class="fa fa-check"></i> Сохранено';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28c76f;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 9999;
        `;
        
        document.body.appendChild(indicator);
        return indicator;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Находим lecture ID из скрытого поля
    const lectureIdInput = document.querySelector('#lecture-id');
    const lectureId = lectureIdInput ? lectureIdInput.value : null;
    
    // Инициализируем менеджер блоков
    window.lectureBlocksManager = new LectureBlocksManager({
        lectureId: lectureId
    });
});

} // Закрываем условный блок защиты от повторного объявления

// Глобальная функция для инициализации (если нужно вызывать вручную)
window.initLectureBlocksManager = (options = {}) => {
    return new LectureBlocksManager(options);
};
