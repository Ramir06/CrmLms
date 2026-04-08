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
            const eventId = info.event.id;
            if (eventId) {
                loadLessonDrawer(eventId);
            }
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
            const eventId = info.event.id;
            if (eventId) {
                loadLessonDrawer(eventId);
            }
        }
    });

    calendar.render();
}
