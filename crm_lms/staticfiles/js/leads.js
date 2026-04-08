
/* ===== CRM LMS — Leads Kanban drag-and-drop ===== */

document.addEventListener('DOMContentLoaded', function () {
    console.log('Loading leads.js...');
    
    // Обработка галочек у лидов и статусов
    const leadCheckboxes = document.querySelectorAll('.lead-checkbox');
    const statusCheckboxes = document.querySelectorAll('.status-checkbox');
    const bulkActions = document.getElementById('bulk-actions');
    const bulkDeleteBtn = document.getElementById('bulk-delete');
    
    console.log('Found lead checkboxes:', leadCheckboxes.length);
    console.log('Found status checkboxes:', statusCheckboxes.length);
    console.log('Found bulk actions:', bulkActions);
    
    function updateBulkActions() {
        const selectedLeads = document.querySelectorAll('.lead-checkbox:checked');
        
        if (selectedLeads.length > 0) {
            bulkActions.style.display = 'block';
            bulkDeleteBtn.textContent = selectedLeads.length === 1 ? 'Удалить выбранного' : `Удалить выбранных (${selectedLeads.length})`;
        } else {
            bulkActions.style.display = 'none';
        }
    }
    
    // Обработка галочек лидов
    leadCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            console.log('Lead checkbox changed:', this.checked);
            updateBulkActions();
            updateStatusCheckbox(this);
        });
    });
    
    // Обработка глобальных галочек статусов
    statusCheckboxes.forEach(function(checkbox) {
        console.log('Setting up status checkbox:', checkbox.dataset.status);
        checkbox.addEventListener('change', function() {
            console.log('Status checkbox changed:', this.checked);
            const status = this.dataset.status;
            const actionsDiv = document.getElementById('status-actions-' + status);
            const column = document.getElementById('col-' + status);
            const leadCheckboxesInColumn = column.querySelectorAll('.lead-checkbox');
            
            console.log('Looking for elements:');
            console.log('- status-actions-' + status, document.getElementById('status-actions-' + status));
            console.log('- col-' + status, document.getElementById('col-' + status));
            console.log('Lead checkboxes in column:', leadCheckboxesInColumn.length);
            
            leadCheckboxesInColumn.forEach(function(leadCheckbox) {
                leadCheckbox.checked = checkbox.checked;
            });
            
            if (this.checked) {
                if (actionsDiv) {
                    actionsDiv.style.display = 'block';
                    console.log('Showing actions for status:', status);
                } else {
                    console.error('Actions div not found for status:', status);
                }
            } else {
                if (actionsDiv) {
                    actionsDiv.style.display = 'none';
                    console.log('Hiding actions for status:', status);
                } else {
                    console.error('Actions div not found for status:', status);
                }
            }
            
            updateBulkActions();
        });
    });
    
    // Обновление галочки статуса на основе лидов в колонке
    function updateStatusCheckbox(changedLeadCheckbox) {
        const card = changedLeadCheckbox.closest('.kanban-card');
        const column = card.closest('.kanban-cards');
        const status = column.dataset.status;
        const statusCheckbox = document.getElementById('status-' + status);
        
        if (statusCheckbox) {
            const leadCheckboxesInColumn = column.querySelectorAll('.lead-checkbox');
            const checkedCount = column.querySelectorAll('.lead-checkbox:checked').length;
            
            if (checkedCount === 0) {
                statusCheckbox.checked = false;
                statusCheckbox.indeterminate = false;
            } else if (checkedCount === leadCheckboxesInColumn.length) {
                statusCheckbox.checked = true;
                statusCheckbox.indeterminate = false;
            } else {
                statusCheckbox.checked = false;
                statusCheckbox.indeterminate = true;
            }
        }
    }
    
    // Инициализация состояния галочек статусов
    statusCheckboxes.forEach(function(statusCheckbox) {
        const status = statusCheckbox.dataset.status;
        const column = document.getElementById('col-' + status);
        const leadCheckboxesInColumn = column.querySelectorAll('.lead-checkbox');
        const checkedCount = column.querySelectorAll('.lead-checkbox:checked').length;
        
        if (checkedCount === 0) {
            statusCheckbox.checked = false;
            statusCheckbox.indeterminate = false;
        } else if (checkedCount === leadCheckboxesInColumn.length) {
            statusCheckbox.checked = true;
            statusCheckbox.indeterminate = false;
        } else {
            statusCheckbox.checked = false;
            statusCheckbox.indeterminate = true;
        }
    });
    
    // Обработка массового удаления
    bulkDeleteBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const selectedLeads = document.querySelectorAll('.lead-checkbox:checked');
        if (selectedLeads.length === 0) return;
        
        if (confirm(`Вы уверены, что хотите удалить ${selectedLeads.length} лид(а/ов)?`)) {
            const leadIds = Array.from(selectedLeads).map(cb => cb.value);
            
            // AJAX запрос для удаления
            fetch('/admin/leads/bulk-delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    lead_ids: leadIds
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Убираем карточки со страницы
                    selectedLeads.forEach(checkbox => {
                        const card = checkbox.closest('.kanban-card');
                        if (card) {
                            card.remove();
                        }
                    });
                    
                    // Обновляем счетчики в заголовках
                    updateStatusCounts();
                    
                    updateBulkActions();
                    
                    // Показываем сообщение об успехе
                    showNotification('Лиды успешно удалены', 'success');
                } else {
                    showNotification('Ошибка при удалении лидов', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Ошибка при удалении лидов', 'error');
            });
        }
    });
    
    // Функция для получения CSRF токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Функция для удаления всех лидов статуса
    window.deleteStatusLeads = function(status, statusName) {
        const column = document.getElementById('col-' + status);
        const leadCheckboxesInColumn = column.querySelectorAll('.lead-checkbox');
        const leadIds = Array.from(leadCheckboxesInColumn).map(cb => cb.value);
        
        if (leadIds.length === 0) {
            showNotification('В этом статусе нет лидов для удаления', 'warning');
            return;
        }
        
        if (confirm(`Вы уверены, что хотите удалить все лиды (${leadIds.length} шт.) из статуса "${statusName}"?`)) {
            // AJAX запрос для удаления всех лидов в статусе
            fetch('/admin/leads/delete-status-leads/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    status_slug: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Убираем все карточки из колонки
                    leadCheckboxesInColumn.forEach(checkbox => {
                        const card = checkbox.closest('.kanban-card');
                        if (card) {
                            card.remove();
                        }
                    });
                    
                    // Обновляем счетчик в заголовке
                    const badge = column.closest('.kanban-col').querySelector('.badge');
                    if (badge) {
                        badge.textContent = '0';
                    }
                    
                    // Скрываем галочку статуса и кнопки действий
                    const statusCheckbox = document.getElementById('status-' + status);
                    const actionsDiv = document.getElementById('status-actions-' + status);
                    if (statusCheckbox) {
                        statusCheckbox.checked = false;
                        statusCheckbox.indeterminate = false;
                    }
                    if (actionsDiv) {
                        actionsDiv.style.display = 'none';
                    }
                    
                    updateBulkActions();
                    
                    // Показываем сообщение об успехе
                    showNotification(`Все лиды из статуса "${statusName}" удалены (${leadIds.length} шт.)`, 'success');
                } else {
                    showNotification('Ошибка при удалении лидов', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Ошибка при удалении лидов', 'error');
            });
        }
    };

    // Функция для обновления счетчиков статусов
    function updateStatusCounts() {
        statusCheckboxes.forEach(function(statusCheckbox) {
            const status = statusCheckbox.dataset.status;
            const column = document.getElementById('col-' + status);
            const badge = column.closest('.kanban-col').querySelector('.badge');
            const count = column.querySelectorAll('.kanban-card').length;
            
            if (badge) {
                badge.textContent = count;
            }
        });
    }
    
    // Функция для показа уведомлений
    function showNotification(message, type) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически убираем через 3 секунды
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    const cards = document.querySelectorAll('.kanban-card');
    const columns = document.querySelectorAll('.kanban-cards');
    let draggedCard = null;
    let draggedLeadId = null;

    // Drag events on cards
    cards.forEach(function (card) {
        card.setAttribute('draggable', 'true');

        card.addEventListener('dragstart', function (e) {
            draggedCard = card;
            draggedLeadId = card.dataset.leadId;
            card.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        card.addEventListener('dragend', function () {
            card.classList.remove('dragging');
            columns.forEach(col => col.classList.remove('drag-over'));
            draggedCard = null;
        });
    });

    // Drop events on columns
    columns.forEach(function (col) {
        col.addEventListener('dragover', function (e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            col.classList.add('drag-over');
        });

        col.addEventListener('dragleave', function () {
            col.classList.remove('drag-over');
        });

        col.addEventListener('drop', function (e) {
            e.preventDefault();
            col.classList.remove('drag-over');

            if (!draggedCard || !draggedLeadId) return;

            const newStatus = col.dataset.status;
            if (!newStatus) return;

            // Move card visually
            col.appendChild(draggedCard);

            // Remove empty placeholder if exists
            const empty = col.querySelector('.kanban-empty');
            if (empty) empty.remove();

            // Send AJAX to backend
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            const token = csrfToken ? csrfToken.value : getCookie('csrftoken');

            fetch(`/admin/leads/${draggedLeadId}/move/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': token,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: `status=${encodeURIComponent(newStatus)}`
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // Update status badge on the card
                    const statusBadge = draggedCard.querySelector('.kanban-card-status');
                    if (statusBadge) {
                        // Get status name from column header or data
                        const statusName = col.closest('.kanban-col').querySelector('.kanban-col-header h6').textContent.trim();
                        statusBadge.textContent = statusName;
                        
                        // Update badge color based on new status
                        const statusColor = col.closest('.kanban-col').querySelector('.kanban-col-header').dataset.color;
                        statusBadge.className = `kanban-card-status badge ${statusColor}`;
                    }
                    
                    // Show success feedback
                    draggedCard.style.animation = 'pulse 0.5s';
                    setTimeout(() => {
                        draggedCard.style.animation = '';
                    }, 500);
                } else {
                    console.warn('Move failed:', data);
                    // Show error feedback
                    draggedCard.style.animation = 'shake 0.5s';
                    setTimeout(() => {
                        draggedCard.style.animation = '';
                    }, 500);
                }
                // Update column counts
                updateColumnCounts();
            })
            .catch(err => {
                console.error('Move error:', err);
                // Show error feedback
                draggedCard.style.animation = 'shake 0.5s';
                setTimeout(() => {
                    draggedCard.style.animation = '';
                }, 500);
            });
        });
    });

    function updateColumnCounts() {
        columns.forEach(function (col) {
            const status = col.dataset.status;
            const header = document.querySelector(`.kanban-col-header[data-status="${status}"] .badge`);
            if (header) {
                header.textContent = col.querySelectorAll('.kanban-card').length;
            }
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
