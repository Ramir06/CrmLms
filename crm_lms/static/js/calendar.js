/* ===== CRM LMS — FullCalendar integration ===== */

function initAdminCalendar(apiUrl) {
    const calEl = document.getElementById('adminCalendar');
    if (!calEl) return;

    const calendar = new FullCalendar.Calendar(calEl, {
        initialView: 'timeGridWeek',
        locale: 'ru',
        firstDay: 1,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridWeek,timeGridDay,listWeek'
        },
        slotMinTime: '07:00:00',
        slotMaxTime: '22:00:00',
        height: 'auto',
        nowIndicator: true,
        eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
        events: function (info, successCallback, failureCallback) {
            const courseFilter = document.getElementById('courseFilter');
            let url = apiUrl + '?start=' + info.startStr + '&end=' + info.endStr;
            if (courseFilter && courseFilter.value) {
                url += '&course=' + courseFilter.value;
            }
            fetch(url)
                .then(r => r.json())
                .then(data => successCallback(data))
                .catch(() => failureCallback());
        },
        eventClick: function (info) {
            const lesson = info.event.extendedProps;
            const title = info.event.title;
            const start = info.event.start;
            const timeStr = start ? start.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' }) : '';

            const eventId = info.event.id;
            const content = `
                <div class="info-list">
                    <div class="info-row"><span class="info-label">Курс</span><span>${lesson.course || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Ментор</span><span>${lesson.mentor || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Время</span><span>${timeStr}</span></div>
                    <div class="info-row"><span class="info-label">Аудитория</span><span>${lesson.room || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Статус</span><span>${lesson.status || '—'}</span></div>
                </div>
                <a href="/calendar/event/${eventId}/drawer/" hx-get="/calendar/event/${eventId}/drawer/" class="btn btn-sm btn-outline-primary w-100 mt-3" onclick="loadLessonDrawer(${eventId}); return false;">
                    <i class="bi bi-people me-1"></i>Посещаемость
                </a>
                ${lesson.meet_link ? '<a href="' + lesson.meet_link + '" target="_blank" class="btn btn-sm btn-primary mt-2 w-100"><i class="bi bi-camera-video me-1"></i>Подключиться</a>' : ''}
            `;
            openDrawer(title, content);
        },
        eventDidMount: function (info) {
            const lesson = info.event.extendedProps;
            if (lesson.status === 'cancelled') {
                info.el.style.opacity = '0.5';
                info.el.style.textDecoration = 'line-through';
            }
        }
    });

    calendar.render();

    const courseFilter = document.getElementById('courseFilter');
    if (courseFilter) {
        courseFilter.addEventListener('change', function () {
            calendar.refetchEvents();
        });
    }
}

function initMentorCalendar(apiUrl) {
    const calEl = document.getElementById('mentorCalendar');
    if (!calEl) return;

    const calendar = new FullCalendar.Calendar(calEl, {
        initialView: 'timeGridWeek',
        locale: 'ru',
        firstDay: 1,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridWeek,timeGridDay,listWeek'
        },
        slotMinTime: '07:00:00',
        slotMaxTime: '22:00:00',
        height: 'auto',
        nowIndicator: true,
        eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
        events: apiUrl,
        eventClick: function (info) {
            const lesson = info.event.extendedProps;
            const timeStr = info.event.start
                ? info.event.start.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
                : '';

            const content = `
                <div class="info-list mb-3">
                    <div class="info-row"><span class="info-label">Курс</span><span>${lesson.course_title || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Время</span><span>${timeStr}</span></div>
                    <div class="info-row"><span class="info-label">Аудитория</span><span>${lesson.room || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Статус</span><span>${lesson.status_display || '—'}</span></div>
                    <div class="info-row"><span class="info-label">Студентов</span><span>${lesson.students_count || 0}</span></div>
                </div>
                <div class="d-flex gap-2">
                    ${lesson.course_id ? '<a href="/course/' + lesson.course_id + '/attendance/?lesson=' + lesson.lesson_id + '" class="btn btn-sm btn-outline-primary w-100"><i class="bi bi-person-check me-1"></i>Посещаемость</a>' : ''}
                </div>
                ${lesson.meet_link ? '<a href="' + lesson.meet_link + '" target="_blank" class="btn btn-sm btn-primary mt-2 w-100"><i class="bi bi-camera-video me-1"></i>Meet</a>' : ''}
            `;
            openDrawer(info.event.title, content);
        }
    });

    calendar.render();
}
