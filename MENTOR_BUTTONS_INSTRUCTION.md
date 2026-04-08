# Инструкция для проверки кнопок "Зайти на урок" и "Открыть чат"

## Что было сделано:

1. **Добавлены кнопки в навбар** - в `templates/includes/navbar.html` добавлены кнопки которые отображаются для ментора когда есть `current_course`

2. **Добавлен current_course во все view ментора** - во всех view связанных с курсами добавлен `current_course` в контекст:
   - `lectures/views.py` - уже было
   - `assignments/views.py` - добавлено
   - `quizzes/views.py` - добавлено  
   - `attendance/views.py` - добавлено
   - `rating/views.py` - добавлено
   - `reviews/views.py` - добавлено
   - `mentors/views_course.py` - уже было

3. **Условия отображения кнопок:**
   - Кнопки показываются только если `current_course` существует
   - Кнопки показываются только если пользователь имеет роль `mentor`
   - Кнопка "Зайти на урок" показывается только если у курса есть `online_lesson_link`
   - Кнопка "Открыть чат" показывается только если у курса есть `chat_link`

## Как проверить:

1. **Зайдите в админ-панель** и создайте/отредактируйте курс
2. **Добавьте ссылки:**
   - Ссылка на онлайн урок (online_lesson_link)
   - Ссылка на чат (chat_link)
3. **Назначьте ментора** на этот курс
4. **Зайдите под аккаунтом ментора** и перейдите в любой раздел курса:
   - Лекции: `/lms/mentor/lectures/courses/<course_id>/lectures/`
   - Задания: `/lms/mentor/assignments/courses/<course_id>/matrix/`
   - Тесты: `/lms/mentor/quizzes/courses/<course_id>/`
   - Посещаемость: `/lms/mentor/attendance/courses/<course_id>/table/`
   - Оценки: `/lms/mentor/rating/courses/<course_id>/`
   - Отзывы: `/lms/mentor/reviews/courses/<course_id>/`

5. **В навбаре вверху** должны появиться кнопки:
   - Красная кнопка "Зайти на урок" (если есть ссылка)
   - Синяя кнопка "Открыть чат" (если есть ссылка)

6. **Кнопки должны:**
   - Открываться в новой вкладке (`target="_blank"`)
   - Быть видны только на десктопе (на мобильных только иконки)
   - Иметь hover эффекты
   - Быть аккуратно стилизованы

## Если кнопки не появляются:

1. Проверьте что у курса заполнены поля `online_lesson_link` и/или `chat_link`
2. Проверьте что вы залогинены как пользователь с ролью `mentor`
3. Проверьте что view передает `current_course` в контекст
4. Откройте консоль браузера и проверьте нет ли ошибок JavaScript

## Технические детали:

- Кнопки используют Bootstrap классы `btn-gradient-danger` и `btn-gradient-info`
- Иконки: `bi-camera-video` и `bi-chat-dots`
- CSS стили добавлены в `navbar.html` для правильного отображения
- Условие: `{% if current_course and request.user.role == 'mentor' %}`
