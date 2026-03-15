/* ===== CRM LMS — Leads Kanban drag-and-drop ===== */

document.addEventListener('DOMContentLoaded', function () {
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

            fetch(`/leads/${draggedLeadId}/move/`, {
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
                if (!data.ok) {
                    console.warn('Move failed:', data);
                }
                // Update column counts
                updateColumnCounts();
            })
            .catch(err => console.error('Move error:', err));
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
