from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta

from apps.core.mixins import mentor_required
from apps.core.mixins_substitute import check_substitute_access, can_mark_attendance
from apps.courses.models import Course, CourseStudent
from apps.lessons.models import Lesson
from .models import AttendanceRecord


def get_mentor_course_with_substitute_access(user, course_id):
    """
    Получение курса с проверкой прав доступа для заменяющего ментора
    """
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)

    course = get_object_or_404(Course, pk=course_id)

    if course.mentor == user:
        return course

    if check_substitute_access(user, course_id):
        return course

    raise PermissionDenied("У вас нет прав доступа к этому курсу")


def _status_consumes_ticket(status):
    """
    Какие статусы списывают талон.
    Если за absent не должно списывать - убери 'absent'.
    """
    return status in ('present', 'absent')


def _get_ticket_info_for_course_student(cs):
    """
    Безопасно получаем информацию о талонах студента
    """
    try:
        ticket_balance = cs.ticket_balance
        return {
            'remaining_tickets': ticket_balance.remaining_tickets,
            'total_tickets': ticket_balance.total_tickets,
            'used_tickets': ticket_balance.used_tickets,
        }
    except Exception:
        return {
            'remaining_tickets': 0,
            'total_tickets': 0,
            'used_tickets': 0,
        }


def _get_course_lessons_for_color_recalculation(course):
    """
    Все занятия курса, участвующие в расчёте цветов
    """
    return list(
        Lesson.objects.filter(course=course)
        .exclude(status='cancelled')
        .order_by('lesson_date', 'start_time', 'id')
    )


def _get_student_attendance_records_for_course(course, student_id):
    """
    Все записи посещаемости конкретного студента по курсу
    """
    return list(
        AttendanceRecord.objects.filter(
            lesson__course=course,
            student_id=student_id
        ).select_related('lesson', 'student').order_by(
            'lesson__lesson_date',
            'lesson__start_time',
            'lesson__id',
            'id'
        )
    )


def _get_total_tickets_for_student_in_course(course, student_id):
    """
    Получаем общее число талонов.
    ВАЖНО:
    Здесь используется total_tickets из ticket_balance.
    Если у тебя в системе total_tickets = "всего куплено за всё время",
    то пересчёт будет работать как последовательный Excel-отчёт:
    первые N списаний зелёные, остальные красные.

    Если у тебя есть история пополнений по датам и нужен расчёт строго
    по датам пополнения, тогда нужно будет подключить модель транзакций.
    """
    try:
        cs = CourseStudent.objects.get(
            course=course,
            student_id=student_id,
            status='active'
        )
        ticket_balance = cs.ticket_balance
        return int(ticket_balance.total_tickets or 0)
    except Exception:
        return 0


def _clear_record_color(record):
    """
    Очистка цветового статуса
    """
    if getattr(record, 'color_status', ''):
        record.color_status = ''
        record.save(update_fields=['color_status'])


def _set_record_color(record, color):
    """
    Установка цвета записи, только если он реально изменился
    """
    if getattr(record, 'color_status', '') != color:
        record.color_status = color
        record.save(update_fields=['color_status'])


def recalculate_student_colors(course, student_id, logger=None):
    """
    ПРАВИЛЬНЫЙ пересчёт цветов для бесконечного курса.

    Логика:
    - Берём все уроки по порядку
    - Берём все attendance записи студента по этому курсу
    - Считаем, сколько талонов у него всего
    - Идём по урокам последовательно
    - Каждый статус, который "списывает талон", использует 1 талон
    - Пока талоны есть -> green
    - Когда талоны закончились -> red

    Это даёт одинаковую последовательность и для таблицы, и для Excel.
    """

    lessons = _get_course_lessons_for_color_recalculation(course)
    records = _get_student_attendance_records_for_course(course, student_id)
    record_map = {(r.lesson_id, r.student_id): r for r in records}

    total_tickets = _get_total_tickets_for_student_in_course(course, student_id)
    consumed_count = 0

    if logger:
        logger.info(
            f"[recalculate_student_colors] start: course={course.id}, "
            f"student={student_id}, total_tickets={total_tickets}, "
            f"lessons={len(lessons)}, records={len(records)}"
        )

    for lesson in lessons:
        rec = record_map.get((lesson.id, student_id))
        if not rec:
            continue

        if _status_consumes_ticket(rec.attendance_status):
            available_before_this_lesson = total_tickets - consumed_count

            if available_before_this_lesson > 0:
                new_color = 'green'
            else:
                new_color = 'red'

            _set_record_color(rec, new_color)

            if logger:
                logger.info(
                    f"[recalculate_student_colors] lesson={lesson.id}, "
                    f"date={lesson.lesson_date}, status={rec.attendance_status}, "
                    f"available_before={available_before_this_lesson}, "
                    f"new_color={new_color}"
                )

            consumed_count += 1
        else:
            _clear_record_color(rec)

            if logger:
                logger.info(
                    f"[recalculate_student_colors] lesson={lesson.id}, "
                    f"date={lesson.lesson_date}, status={rec.attendance_status}, "
                    f"color_cleared=True"
                )


def recalculate_many_students_colors(course, student_ids, logger=None):
    """
    Пересчёт цветов сразу для нескольких студентов
    """
    unique_ids = []
    seen = set()

    for student_id in student_ids:
        if student_id and student_id not in seen:
            seen.add(student_id)
            unique_ids.append(student_id)

    for student_id in unique_ids:
        try:
            recalculate_student_colors(course, student_id, logger=logger)
        except Exception as e:
            if logger:
                logger.error(
                    f"[recalculate_many_students_colors] "
                    f"Error recalculating colors for student={student_id}: {str(e)}"
                )


def _get_student_ids_from_post_data(post_data):
    """
    Вытаскиваем все student_id из POST данных формата att_<lesson_id>_<student_id>
    """
    student_ids = set()

    for key in post_data.keys():
        if not key.startswith('att_'):
            continue

        parts = key.split('_')
        if len(parts) != 3:
            continue

        try:
            student_id = int(parts[2])
            student_ids.add(student_id)
        except ValueError:
            continue

    return student_ids


def _get_lesson_ids_from_post_data(post_data):
    """
    Вытаскиваем все lesson_id из POST данных формата att_<lesson_id>_<student_id>
    """
    lesson_ids = set()

    for key in post_data.keys():
        if not key.startswith('att_'):
            continue

        parts = key.split('_')
        if len(parts) != 3:
            continue

        try:
            lesson_id = int(parts[1])
            lesson_ids.add(lesson_id)
        except ValueError:
            continue

    return lesson_ids


def _save_single_attendance_value(request, course, lesson_id, student_id, value, logger=None):
    """
    Сохраняет одну attendance-запись и возвращает словарь с результатом.
    """
    old_record = AttendanceRecord.objects.filter(
        lesson_id=lesson_id,
        student_id=student_id
    ).first()

    old_status = old_record.attendance_status if old_record else ''
    old_color_status = old_record.color_status if old_record else ''
    old_consumes = _status_consumes_ticket(old_status)
    new_consumes = _status_consumes_ticket(value)

    attendance_record, created = AttendanceRecord.objects.update_or_create(
        lesson_id=lesson_id,
        student_id=student_id,
        defaults={
            'attendance_status': value,
            'marked_by': request.user if value else None,
        },
    )

    if logger:
        logger.info(
            f"[save_single_attendance] lesson_id={lesson_id}, student_id={student_id}, "
            f"old_status='{old_status}', new_status='{value}', "
            f"old_color='{old_color_status}', created={created}, "
            f"old_consumes={old_consumes}, new_consumes={new_consumes}"
        )

    return {
        'attendance_record': attendance_record,
        'created': created,
        'old_record': old_record,
        'old_status': old_status,
        'old_color_status': old_color_status,
        'old_consumes': old_consumes,
        'new_consumes': new_consumes,
    }


def _create_lesson_debt(course_student, lesson_id, marked_by_user, logger=None):
    """
    Создает долг типа "Занятие" для студента при перерасходе талонов
    """
    try:
        from apps.debts.models import Debt
        from django.utils import timezone
        
        # Получаем текущий месяц и год
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # Определяем цену за занятие
        # Для бесконечных курсов используем цену курса / длительность в месяцах, но не менее 1
        course = course_student.course
        if course.duration_months and course.duration_months > 0:
            lesson_price = course.price / course.duration_months
        else:
            lesson_price = course.price / 3  # По умолчанию делим на 3 месяца
        
        # Убеждаемся, что цена не меньше 1
        lesson_price = max(lesson_price, 1)
        
        # Проверяем, есть ли уже долг типа "Занятие" за текущий месяц
        existing_debt = Debt.objects.filter(
            student=course_student.student,
            course=course_student.course,
            debt_type='lesson',
            month=current_month,
            year=current_year,
            status='active'
        ).first()
        
        if existing_debt:
            # Если долг уже существует, увеличиваем сумму
            existing_debt.total_amount += lesson_price
            existing_debt.note += f"\n+ Урок {lesson_id} ({timezone.now().strftime('%d.%m.%Y')})"
            existing_debt.save()
            
            if logger:
                logger.info(
                    f"[create_lesson_debt] Updated existing lesson debt: "
                    f"student={course_student.student_id}, lesson={lesson_id}, "
                    f"new_total={existing_debt.total_amount}"
                )
        else:
            # Создаем новый долг типа "Занятие"
            debt = Debt.objects.create(
                student=course_student.student,
                course=course_student.course,
                total_amount=lesson_price,
                paid_amount=0,
                status='active',
                debt_type='lesson',
                month=current_month,
                year=current_year,
                note=f'Долг за посещение занятия без талонов. Урок {lesson_id} ({timezone.now().strftime('%d.%m.%Y')})'
            )
            
            if logger:
                logger.info(
                    f"[create_lesson_debt] Created new lesson debt: "
                    f"student={course_student.student_id}, lesson={lesson_id}, "
                    f"amount={lesson_price}"
                )
                
    except Exception as e:
        if logger:
            logger.error(
                f"[create_lesson_debt] Error creating lesson debt for "
                f"student={course_student.student_id}, lesson={lesson_id}: {str(e)}"
            )


def _try_consume_ticket_for_unlimited_course(course, lesson_id, student_id, marked_by_user, logger=None):
    """
    Пытаемся списать талон только в момент перехода записи в consuming status.
    Защита:
    - не падаем, если баланса нет
    - не падаем, если ticket_balance отсутствует
    """
    try:
        from apps.courses.services import TicketService
    except Exception as e:
        if logger:
            logger.error(f"[try_consume_ticket] Cannot import TicketService: {str(e)}")
        return False

    cs = CourseStudent.objects.filter(
        course=course,
        student_id=student_id,
        status='active'
    ).first()

    if not cs:
        if logger:
            logger.warning(
                f"[try_consume_ticket] No active CourseStudent for student_id={student_id}, course={course.id}"
            )
        return False

    try:
        current_balance = cs.ticket_balance
        remaining_tickets = int(current_balance.remaining_tickets or 0)
        total_tickets = int(current_balance.total_tickets or 0)
        used_tickets = int(current_balance.used_tickets or 0)
    except Exception as e:
        if logger:
            logger.error(
                f"[try_consume_ticket] Cannot get ticket_balance for "
                f"student_id={student_id}: {str(e)}"
            )
        return False

    # Проверяем перерасход: использовано больше чем куплено, или остаток отрицательный
    has_overdue = (used_tickets > total_tickets) or (remaining_tickets < 0)

    if has_overdue:
        if logger:
            logger.warning(
                f"[try_consume_ticket] Ticket overdue detected for student_id={student_id}, "
                f"course={course.id}. Total: {total_tickets}, Used: {used_tickets}, "
                f"Remaining: {remaining_tickets}. Creating lesson debt."
            )
        
        # Создаем долг типа "Занятие" при перерасходе талонов
        _create_lesson_debt(cs, lesson_id, marked_by_user, logger)
        return False

    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        if logger:
            logger.error(f"[try_consume_ticket] Lesson does not exist: lesson_id={lesson_id}")
        return False

    try:
        TicketService.consume_tickets(
            enrollment=cs,
            lessons_count=1,
            marked_by=marked_by_user,
            lesson_date=lesson.lesson_date,
            comment=f"Автоматическое списание за урок {lesson_id}"
        )

        if logger:
            logger.info(
                f"[try_consume_ticket] Ticket consumed successfully: "
                f"student_id={student_id}, lesson_id={lesson_id}"
            )

        return True

    except Exception as e:
        if logger:
            logger.error(
                f"[try_consume_ticket] Error consuming ticket for "
                f"student_id={student_id}, lesson_id={lesson_id}: {str(e)}"
            )
        return False


def _handle_unlimited_course_logic_after_save(
    request,
    course,
    lesson_id,
    student_id,
    value,
    save_result,
    logger=None
):
    """
    Логика после сохранения записи для бесконечного курса.

    ВАЖНО:
    Мы больше НЕ оставляем "старый цвет как есть".
    Цвет будет корректно пересчитан позже через recalculate_student_colors().

    Здесь:
    - если статус очищен -> можно временно очистить color_status
    - если статус стал consuming, а раньше не был -> пробуем списать талон
    - если статус перестал списывать -> просто очистим цвет, потом пересчёт всё нормализует
    - если статус consuming и у студента нет талонов -> создаем долг
    """
    attendance_record = save_result['attendance_record']
    old_consumes = save_result['old_consumes']
    new_consumes = save_result['new_consumes']

    # Если статус очищен
    if not value:
        attendance_record.color_status = ''
        attendance_record.save(update_fields=['color_status'])

        if logger:
            logger.info(
                f"[handle_unlimited_logic] cleared status/color "
                f"for lesson={lesson_id}, student={student_id}"
            )
        return

    # Если раньше НЕ списывал, а теперь списывает
    if (not old_consumes) and new_consumes:
        result = _try_consume_ticket_for_unlimited_course(
            course=course,
            lesson_id=lesson_id,
            student_id=student_id,
            marked_by_user=request.user,
            logger=logger
        )
        
        # Если талонов не хватило, создаем долг
        if not result:
            _create_lesson_debt_for_attendance(
                course, lesson_id, student_id, request.user, logger
            )
        return

    # Если раньше списывал, а теперь нет
    if old_consumes and (not new_consumes):
        attendance_record.color_status = ''
        attendance_record.save(update_fields=['color_status'])

        if logger:
            logger.info(
                f"[handle_unlimited_logic] consuming -> non-consuming, "
                f"color cleared for lesson={lesson_id}, student={student_id}"
            )
        return

    # Если раньше списывал и сейчас списывает
    # Проверяем, нужно ли создать долг (если талонов закончились)
    if old_consumes and new_consumes:
        # Проверяем баланс талонов
        cs = CourseStudent.objects.filter(
            course=course,
            student_id=student_id,
            status='active'
        ).first()
        
        if cs:
            try:
                current_balance = cs.ticket_balance
                remaining_tickets = int(current_balance.remaining_tickets or 0)
                total_tickets = int(current_balance.total_tickets or 0)
                used_tickets = int(current_balance.used_tickets or 0)
                
                # Проверяем перерасход: использовано больше чем куплено, или остаток отрицательный
                has_overdue = (used_tickets > total_tickets) or (remaining_tickets < 0)
                
                if has_overdue:
                    # У студента перерасход талонов, создаем долг
                    _create_lesson_debt_for_attendance(
                        course, lesson_id, student_id, request.user, logger
                    )
                    
                    if logger:
                        logger.info(
                            f"[handle_unlimited_logic] consuming -> consuming, "
                            f"negative balance detected, creating debt "
                            f"for lesson={lesson_id}, student={student_id}"
                        )
            except Exception as e:
                if logger:
                    logger.error(f"[handle_unlimited_logic] Error checking balance: {str(e)}")
        
        if logger:
            logger.info(
                f"[handle_unlimited_logic] consuming -> consuming, "
                f"skip immediate color save, wait recalculation "
                f"for lesson={lesson_id}, student={student_id}"
            )
        return


def _create_lesson_debt_for_attendance(course, lesson_id, student_id, marked_by_user, logger=None):
    """
    Создает долг типа "Занятие" для студента при посещении без талонов
    """
    try:
        cs = CourseStudent.objects.filter(
            course=course,
            student_id=student_id,
            status='active'
        ).first()
        
        if cs:
            _create_lesson_debt(cs, lesson_id, marked_by_user, logger)
            
    except Exception as e:
        if logger:
            logger.error(f"[create_lesson_debt_for_attendance] Error: {str(e)}")


def _create_debts_for_existing_overdue_attendance(course, logger=None):
    """
    Создает долги для существующих посещений с перерасходом талонов
    """
    try:
        from apps.courses.models import CourseStudent
        from apps.courses.tickets import TicketBalance
        
        # Получаем всех активных студентов на бесконечных курсах
        enrollments = CourseStudent.objects.filter(
            course=course,
            status='active'
        ).select_related('student', 'course').prefetch_related('ticket_balance')
        
        for enrollment in enrollments:
            try:
                ticket_balance = enrollment.ticket_balance
                if ticket_balance is None:
                    continue
                
                # Проверяем баланс
                remaining_tickets = int(ticket_balance.remaining_tickets or 0)
                total_tickets = int(ticket_balance.total_tickets or 0)
                used_tickets = int(ticket_balance.used_tickets or 0)
                
                # Проверяем перерасход: использовано больше чем куплено, или остаток отрицательный
                has_overdue = (used_tickets > total_tickets) or (remaining_tickets < 0)
                
                if has_overdue:
                    # У студента есть перерасход, проверяем посещения
                    from apps.attendance.models import AttendanceRecord
                    
                    attendance_records = AttendanceRecord.objects.filter(
                        lesson__course=course,
                        student=enrollment.student,
                        attendance_status='present'  # Только посещенные занятия
                    ).order_by('lesson__lesson_date')
                    
                    # Создаем долги за посещения сверх талонов
                    total_tickets = int(ticket_balance.total_tickets or 0)
                    paid_visits = 0
                    
                    for record in attendance_records:
                        if paid_visits < total_tickets:
                            paid_visits += 1
                        else:
                            # Это посещение сверх талонов, создаем долг
                            _create_lesson_debt(
                                enrollment, 
                                record.lesson_id, 
                                None,  # marked_by_user
                                logger
                            )
                    
                    if logger:
                        logger.info(
                            f"[create_debts_for_existing] Created debts for "
                            f"student={enrollment.student.full_name}, "
                            f"overdue_visits={len(attendance_records) - total_tickets}"
                        )
                        
            except Exception as e:
                if logger:
                    logger.error(f"[create_debts_for_existing] Error for student {enrollment.student_id}: {str(e)}")
                continue
                    
    except Exception as e:
        if logger:
            logger.error(f"[create_debts_for_existing] General error: {str(e)}")


@login_required
@mentor_required
def attendance_table(request, course_id):
    response = None

    course = get_mentor_course_with_substitute_access(request.user, course_id)

    # Получаем параметры недели
    today = date.today()
    week_offset = int(request.GET.get('week', 0))
    
    # Создаем данные для 3 недель
    weeks_data = []
    for i in range(-1, 2):  # -1, 0, 1 (предыдущая, текущая, следующая)
        week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset + i)
        week_end = week_start + timedelta(days=6)
        
        # Фильтруем уроки за эту неделю
        lessons = Lesson.objects.filter(
            course=course,
            lesson_date__gte=week_start,
            lesson_date__lte=week_end
        ).exclude(status='cancelled').order_by('lesson_date', 'start_time', 'id')

        # Для заменяющего ментора фильтруем уроки только по дням замен
        if course.mentor != request.user and request.user.role == 'mentor':
            from apps.lessons.models_substitute import MentorSubstitution
            substitution_lesson_ids = MentorSubstitution.objects.filter(
                substitute_mentor=request.user,
                status='confirmed',
                lesson__course=course
            ).values_list('lesson_id', flat=True)
            lessons = lessons.filter(id__in=substitution_lesson_ids)

        weeks_data.append({
            'week_start': week_start,
            'week_end': week_end,
            'lessons': lessons,
            'week_offset': week_offset + i
        })

    students = CourseStudent.objects.filter(
        course=course,
        status='active'
    ).select_related('student').order_by('student__full_name')

    # Создаем матрицу для всех 3 недель
    all_lessons = []
    for week_data in weeks_data:
        all_lessons.extend(week_data['lessons'])

    records = AttendanceRecord.objects.filter(
        lesson__in=all_lessons
    ).select_related('student', 'lesson')

    record_map = {(r.lesson_id, r.student_id): r for r in records}

    matrix = []
    for cs in students:
        ticket_info = _get_ticket_info_for_course_student(cs) if course.is_unlimited else None

        row = {
            'cs': cs,
            'weeks_cells': [],
            'ticket_info': ticket_info
        }

        # Создаем ячейки для каждой недели
        for week_data in weeks_data:
            week_cells = []
            total_lessons = len(week_data['lessons'])
            present_count = 0

            for lesson in week_data['lessons']:
                rec = record_map.get((lesson.pk, cs.student_id))
                can_mark = can_mark_attendance(request.user, lesson.pk)

                week_cells.append({
                    'lesson_id': lesson.pk,
                    'record': rec,
                    'status': rec.attendance_status if rec else '',
                    'color_status': rec.color_status if rec else '',
                    'can_mark': can_mark,
                    'marked_by': rec.marked_by if rec else None,
                    'marked_by_display': rec.marked_by_display if rec else None,
                })

                if rec and rec.attendance_status == 'present':
                    present_count += 1

            week_percent = round((present_count / total_lessons) * 100) if total_lessons > 0 else 0
            row['weeks_cells'].append({
                'cells': week_cells,
                'percent': week_percent,
                'total_lessons': total_lessons
            })

        matrix.append(row)

    context = {
        'course': course,
        'current_course': course,
        'lessons': [lesson for week_data in weeks_data for lesson in week_data['lessons']],  # Для совместимости со старым шаблоном
        'weeks_data': weeks_data,
        'matrix': matrix,
        'STATUS_CHOICES': AttendanceRecord.STATUS_CHOICES,
        'page_title': 'Посещаемость',
        'active_menu': 'attendance',
        'is_substitute_mentor': course.mentor != request.user and request.user.role == 'mentor',
        'current_week': week_offset,
        'prev_week': week_offset - 1,
        'next_week': week_offset + 1,
    }

    response = render(request, 'mentor/attendance/table.html', context)

    if response:
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response


def test_view(request):
    """Тестовая view для проверки работы URL"""
    print("!!! TEST VIEW CALLED !!!", flush=True)
    return JsonResponse({'success': True, 'message': 'Test view works!'})


def test_save_view(request):
    """Тестовая view для проверки POST запросов"""
    print("!!! TEST SAVE VIEW CALLED !!!", flush=True)
    print(f"!!! METHOD: {request.method} !!!", flush=True)
    print(f"!!! POST DATA: {dict(request.POST)} !!!", flush=True)
    return JsonResponse({
        'success': True,
        'message': 'Test save view works!',
        'post_data': dict(request.POST)
    })


@login_required
@mentor_required
@require_POST
@transaction.atomic
def save_attendance_bulk(request, course_id):
    """Массовое сохранение посещаемости для всех студентов курса"""

    import logging
    logger = logging.getLogger(__name__)

    try:
        from apps.lessons.models_substitute import MentorSubstitution

        course = get_mentor_course_with_substitute_access(request.user, course_id)

        active_students = CourseStudent.objects.filter(
            course=course,
            status='active'
        ).values_list('student_id', flat=True)

        active_student_ids = set(active_students)

        touched_lesson_ids = set()
        touched_student_ids = set()

        for key, value in request.POST.items():

            if not key.startswith('att_'):
                continue

            parts = key.split('_')
            if len(parts) != 3:
                continue

            try:
                lesson_id = int(parts[1])
                student_id = int(parts[2])
            except ValueError:
                continue

            try:
                can_mark = can_mark_attendance(request.user, lesson_id)

                if not can_mark:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': f'У вас нет прав для отметки посещаемости урока {lesson_id}'
                        })

                    messages.error(request, f'У вас нет прав для отметки посещаемости урока {lesson_id}')
                    continue

                save_result = _save_single_attendance_value(
                    request=request,
                    course=course,
                    lesson_id=lesson_id,
                    student_id=student_id,
                    value=value,
                    logger=logger
                )

                attendance_record = save_result['attendance_record']

                try:
                    saved_record = AttendanceRecord.objects.get(
                        lesson_id=lesson_id,
                        student_id=student_id
                    )
                    logger.info(
                        f"Verification - saved record: status='{saved_record.attendance_status}', "
                        f"marked_by={saved_record.marked_by.username if saved_record.marked_by else None}"
                    )
                except AttendanceRecord.DoesNotExist:
                    logger.error("ERROR: Record not found after saving!")

                if course.is_unlimited:
                    _handle_unlimited_course_logic_after_save(
                        request=request,
                        course=course,
                        lesson_id=lesson_id,
                        student_id=student_id,
                        value=value,
                        save_result=save_result,
                        logger=logger
                    )
                else:
                    # Для обычного курса цвет не нужен
                    if getattr(attendance_record, 'color_status', ''):
                        attendance_record.color_status = ''
                        attendance_record.save(update_fields=['color_status'])

                touched_lesson_ids.add(lesson_id)
                touched_student_ids.add(student_id)

            except Exception as e:
                logger.error(f"Error processing attendance data: {str(e)}")
                continue

        # Самое важное:
        # после всех сохранений ПЕРЕСЧИТЫВАЕМ цвета для затронутых студентов
        if course.is_unlimited and touched_student_ids:
            logger.info(
                f"Recalculating colors for touched students: {list(touched_student_ids)}"
            )
            recalculate_many_students_colors(
                course=course,
                student_ids=touched_student_ids,
                logger=logger
            )
            
            # Дополнительная проверка: создаем долги для существующих перерасходов
            logger.info("Checking for existing overdue attendance...")
            _create_debts_for_existing_overdue_attendance(
                course=course,
                logger=logger
            )

        # Auto-complete lessons where 90%+ of active students have been marked
        for lesson_id in touched_lesson_ids:
            try:
                lesson = Lesson.objects.get(pk=lesson_id, course=course)

                marked_students = set(
                    AttendanceRecord.objects.filter(lesson=lesson)
                    .exclude(attendance_status='')
                    .values_list('student_id', flat=True)
                )

                # Check if 90%+ of active students are marked
                if active_student_ids and len(active_student_ids) > 0:
                    marked_percentage = len(marked_students & active_student_ids) / len(active_student_ids) * 100
                    
                    if marked_percentage >= 90 and lesson.status == 'scheduled':
                        lesson.status = 'completed'
                        lesson.save(update_fields=['status'])

                        try:
                            substitution = MentorSubstitution.objects.get(
                                lesson=lesson,
                                substitute_mentor=request.user,
                                status='confirmed'
                            )
                            substitution.complete()
                        except MentorSubstitution.DoesNotExist:
                            pass

            except Lesson.DoesNotExist:
                pass

        if (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        ):
            logger.info("Returning AJAX response with success=True")
            return JsonResponse({
                'success': True,
                'message': 'Посещаемость успешно сохранена'
            })

        return redirect('attendance:table', course_id=course_id)

    except Exception as e:
        error_message = f"Ошибка при сохранении посещаемости: {str(e)}"
        logger.error(error_message)

        if (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        ):
            return JsonResponse({'success': False, 'error': error_message})

        messages.error(request, error_message)
        return redirect('attendance:table', course_id=course_id)