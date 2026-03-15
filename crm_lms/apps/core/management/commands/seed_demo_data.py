import random
from datetime import date, timedelta, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with demo data for CRM/LMS project'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Flush existing data before seeding')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing non-superuser data...'))
            self._flush_data()

        self.stdout.write('Creating demo users...')
        admin_user, mentor_user1, mentor_user2 = self._create_users()

        self.stdout.write('Creating mentor profiles...')
        self._create_mentors(mentor_user1, mentor_user2)

        self.stdout.write('Creating courses...')
        courses = self._create_courses(mentor_user1, mentor_user2)

        self.stdout.write('Creating students...')
        students = self._create_students()

        self.stdout.write('Creating enrollments...')
        self._create_enrollments(students, courses)

        self.stdout.write('Creating lessons...')
        lessons = self._create_lessons(courses)

        self.stdout.write('Creating attendance...')
        self._create_attendance(lessons)

        self.stdout.write('Creating payments & debts...')
        self._create_payments_and_debts()

        self.stdout.write('Creating salaries...')
        self._create_salaries(mentor_user1, mentor_user2)

        self.stdout.write('Creating finance records...')
        self._create_finance()

        self.stdout.write('Creating leads...')
        self._create_leads(courses)

        self.stdout.write('Creating news...')
        self._create_news(admin_user)

        self.stdout.write('Creating lectures & materials...')
        self._create_lectures(courses)

        self.stdout.write('Creating assignments...')
        self._create_assignments(courses)

        self.stdout.write('Creating reviews...')
        self._create_reviews(courses, admin_user)

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('  Admin:   admin@example.com / admin12345')
        self.stdout.write('  Mentor:  mentor@example.com / mentor12345')
        self.stdout.write('  Mentor2: mentor2@example.com / mentor12345')

    # ─────────────────────────────────────────────────────────────────────────
    def _flush_data(self):
        from apps.assignments.models import AssignmentGrade, AssignmentSubmission, Assignment
        from apps.reviews.models import Review
        from apps.attendance.models import AttendanceRecord
        from apps.courses.models import CourseStudent
        from apps.lessons.models import Lesson
        from apps.payments.models import Payment
        from apps.debts.models import Debt
        from apps.salaries.models import SalaryAccrual
        from apps.finance.models import FinanceTransaction
        from apps.leads.models import Lead, LeadAction
        from apps.news.models import News
        from apps.lectures.models import Material, Section
        from apps.students.models import Student
        from apps.courses.models import Course
        from apps.mentors.models import MentorProfile

        for model in [AssignmentGrade, AssignmentSubmission, Assignment, Review,
                      AttendanceRecord, CourseStudent, Lesson, Payment, Debt,
                      SalaryAccrual, FinanceTransaction, LeadAction, Lead,
                      News, Material, Section, Student, Course, MentorProfile]:
            model.objects.all().delete()

        User.objects.filter(is_superuser=False).delete()

    # ─────────────────────────────────────────────────────────────────────────
    def _create_users(self):
        admin_user, _ = User.objects.get_or_create(
            email='admin@example.com',
            defaults={'role': 'admin', 'first_name': 'Алибек',
                      'last_name': 'Джаксыбеков', 'is_staff': True}
        )
        admin_user.set_password('admin12345')
        admin_user.save()

        mentor_user1, _ = User.objects.get_or_create(
            email='mentor@example.com',
            defaults={'role': 'mentor', 'first_name': 'Дмитрий', 'last_name': 'Петров'}
        )
        mentor_user1.set_password('mentor12345')
        mentor_user1.save()

        mentor_user2, _ = User.objects.get_or_create(
            email='mentor2@example.com',
            defaults={'role': 'mentor', 'first_name': 'Айнур', 'last_name': 'Сейткали'}
        )
        mentor_user2.set_password('mentor12345')
        mentor_user2.save()

        return admin_user, mentor_user1, mentor_user2

    def _create_mentors(self, mentor_user1, mentor_user2):
        from apps.mentors.models import MentorProfile

        MentorProfile.objects.get_or_create(
            user=mentor_user1,
            defaults={
                'specialization': 'Python / Backend',
                'salary_type': 'percent',
                'percent_salary': Decimal('20.00'),
                'bio': 'Senior Python developer with 8 years of experience.',
            }
        )
        MentorProfile.objects.get_or_create(
            user=mentor_user2,
            defaults={
                'specialization': 'Frontend / React',
                'salary_type': 'fixed',
                'fixed_salary': Decimal('150000.00'),
                'bio': 'Frontend developer specializing in React and TypeScript.',
            }
        )

    def _create_courses(self, mentor_user1, mentor_user2):
        from apps.courses.models import Course

        courses_data = [
            {
                'title': 'Python Backend Development',
                'description': 'Полный курс по Python: от основ до Django REST Framework.',
                'mentor': mentor_user1,
                'price': Decimal('120000.00'),
                'capacity': 15,
                'color': '#6366f1',
                'status': 'active',
                'start_date': date.today() - timedelta(days=30),
                'days_of_week': 'mon_wed_fri',
                'lesson_start_time': time(18, 0),
                'lesson_end_time': time(20, 0),
            },
            {
                'title': 'React Frontend Bootcamp',
                'description': 'Интенсивный курс по React, TypeScript и современному фронтенду.',
                'mentor': mentor_user2,
                'price': Decimal('100000.00'),
                'capacity': 12,
                'color': '#10b981',
                'status': 'active',
                'start_date': date.today() - timedelta(days=20),
                'days_of_week': 'tue_thu_sat',
                'lesson_start_time': time(19, 0),
                'lesson_end_time': time(21, 0),
            },
            {
                'title': 'Data Science с Python',
                'description': 'Анализ данных, pandas, matplotlib, machine learning basics.',
                'mentor': mentor_user1,
                'price': Decimal('135000.00'),
                'capacity': 10,
                'color': '#f59e0b',
                'status': 'planned',
                'start_date': date.today() + timedelta(days=14),
                'days_of_week': 'sat_sun',
                'lesson_start_time': time(10, 0),
                'lesson_end_time': time(13, 0),
            },
        ]

        courses = []
        for data in courses_data:
            course, _ = Course.objects.get_or_create(title=data['title'], defaults=data)
            courses.append(course)
        return courses

    def _create_students(self):
        from apps.students.models import Student

        students_data = [
            {'full_name': 'Азиз Мамедов', 'phone': '+7 701 111 22 33', 'source': 'instagram', 'status': 'active'},
            {'full_name': 'Карина Ли', 'phone': '+7 702 222 33 44', 'source': 'referral', 'status': 'active'},
            {'full_name': 'Тимур Асанов', 'phone': '+7 703 333 44 55', 'source': 'website', 'status': 'active'},
            {'full_name': 'Дана Жумабекова', 'phone': '+7 704 444 55 66', 'source': 'instagram', 'status': 'active'},
            {'full_name': 'Антон Белов', 'phone': '+7 705 555 66 77', 'source': 'other', 'status': 'active'},
            {'full_name': 'Зарина Нурова', 'phone': '+7 706 666 77 88', 'source': 'telegram', 'status': 'active'},
            {'full_name': 'Максим Крылов', 'phone': '+7 707 777 88 99', 'source': 'website', 'status': 'active'},
            {'full_name': 'Айгуль Сейтова', 'phone': '+7 708 888 99 00', 'source': 'referral', 'status': 'active'},
            {'full_name': 'Руслан Дюсенов', 'phone': '+7 709 999 00 11', 'source': 'instagram', 'status': 'inactive'},
            {'full_name': 'Виктория Шевченко', 'phone': '+7 710 000 11 22', 'source': 'other', 'status': 'graduated'},
        ]

        students = []
        for data in students_data:
            student, _ = Student.objects.get_or_create(phone=data['phone'], defaults=data)
            students.append(student)
        return students

    def _create_enrollments(self, students, courses):
        from apps.courses.models import CourseStudent

        for i, student in enumerate(students[:8]):
            course = courses[i % 2]
            CourseStudent.objects.get_or_create(
                student=student, course=course,
                defaults={'joined_at': date.today() - timedelta(days=random.randint(5, 25))}
            )

        for student in students[2:5]:
            CourseStudent.objects.get_or_create(
                student=student, course=courses[0],
                defaults={'joined_at': date.today() - timedelta(days=10)}
            )

    def _create_lessons(self, courses):
        from apps.lessons.models import Lesson

        lessons = []
        for course in courses[:2]:
            start_t = course.lesson_start_time or time(18, 0)
            end_t = course.lesson_end_time or time(20, 0)
            for i in range(8):
                lesson_date = date.today() - timedelta(days=i * 3 + 1)
                lesson, _ = Lesson.objects.get_or_create(
                    course=course,
                    lesson_date=lesson_date,
                    start_time=start_t,
                    defaults={
                        'end_time': end_t,
                        'status': 'completed',
                        'room': f'Зал {random.randint(1, 3)}',
                    }
                )
                lessons.append(lesson)
        return lessons

    def _create_attendance(self, lessons):
        from apps.attendance.models import AttendanceRecord
        from apps.courses.models import CourseStudent

        statuses = ['present', 'present', 'present', 'absent', 'late']
        for lesson in lessons:
            enrolled = CourseStudent.objects.filter(course=lesson.course).select_related('student')
            for cs in enrolled:
                AttendanceRecord.objects.get_or_create(
                    lesson=lesson,
                    student=cs.student,
                    defaults={'attendance_status': random.choice(statuses)}
                )

    def _create_payments_and_debts(self):
        from apps.payments.models import Payment
        from apps.debts.models import Debt
        from apps.courses.models import CourseStudent

        for cs in CourseStudent.objects.select_related('student', 'course').all():
            paid = random.choice([True, True, False])
            if paid:
                Payment.objects.get_or_create(
                    student=cs.student,
                    course=cs.course,
                    defaults={
                        'amount': cs.course.price,
                        'paid_at': date.today() - timedelta(days=random.randint(1, 20)),
                        'payment_method': random.choice(['cash', 'card', 'transfer']),
                    }
                )
            else:
                Debt.objects.get_or_create(
                    student=cs.student,
                    course=cs.course,
                    defaults={'total_amount': cs.course.price}
                )

    def _create_salaries(self, mentor_user1, mentor_user2):
        from apps.salaries.models import SalaryAccrual

        today = date.today()
        for i in range(3):
            month_num = today.month - i
            year = today.year
            if month_num <= 0:
                month_num += 12
                year -= 1
            month = date(year, month_num, 1)

            SalaryAccrual.objects.get_or_create(
                mentor=mentor_user1,
                month=month,
                defaults={
                    'amount': Decimal(str(random.randint(80000, 150000))),
                    'paid_status': 'paid' if i > 0 else 'pending',
                }
            )
            SalaryAccrual.objects.get_or_create(
                mentor=mentor_user2,
                month=month,
                defaults={
                    'amount': Decimal('150000.00'),
                    'paid_status': 'paid' if i > 0 else 'pending',
                }
            )

    def _create_finance(self):
        from apps.finance.models import FinanceTransaction

        records = [
            {'type': 'income', 'amount': Decimal('480000'), 'description': 'Оплаты за Python-курс'},
            {'type': 'income', 'amount': Decimal('300000'), 'description': 'Оплаты за React-курс'},
            {'type': 'expense', 'amount': Decimal('150000'), 'description': 'Зарплата — Д. Петров'},
            {'type': 'expense', 'amount': Decimal('150000'), 'description': 'Зарплата — А. Сейткали'},
            {'type': 'expense', 'amount': Decimal('50000'), 'description': 'Аренда офиса'},
            {'type': 'expense', 'amount': Decimal('15000'), 'description': 'Канцтовары и расходники'},
            {'type': 'income', 'amount': Decimal('25000'), 'description': 'Дополнительные занятия'},
        ]

        for i, data in enumerate(records):
            data['transaction_date'] = date.today() - timedelta(days=i * 3)
            FinanceTransaction.objects.get_or_create(
                description=data['description'],
                defaults=data
            )

    def _create_leads(self, courses):
        from apps.leads.models import Lead

        leads_data = [
            {'full_name': 'Нурлан Байжанов', 'phone': '+7 771 100 20 30', 'source': 'instagram', 'status': 'new', 'interested_course': courses[0]},
            {'full_name': 'Алина Ким', 'phone': '+7 772 200 30 40', 'source': 'telegram', 'status': 'consultation', 'interested_course': courses[1]},
            {'full_name': 'Марат Сейткали', 'phone': '+7 773 300 40 50', 'source': 'website', 'status': 'trial_lesson', 'interested_course': courses[0]},
            {'full_name': 'Лейла Абдуллаева', 'phone': '+7 774 400 50 60', 'source': 'referral', 'status': 'enrolling'},
            {'full_name': 'Данияр Ержанов', 'phone': '+7 775 500 60 70', 'source': 'other', 'status': 'rejected'},
            {'full_name': 'Самал Оразова', 'phone': '+7 776 600 70 80', 'source': 'instagram', 'status': 'new', 'interested_course': courses[1]},
        ]

        for data in leads_data:
            Lead.objects.get_or_create(phone=data['phone'], defaults=data)

    def _create_news(self, admin_user):
        from apps.news.models import News

        news_data = [
            {
                'title': 'Добро пожаловать в CRM LMS!',
                'content': 'Рады представить вам нашу новую платформу для управления курсами. Здесь вы найдёте все необходимые инструменты для работы.',
                'audience': 'all',
                'is_published': True,
                'created_by': admin_user,
            },
            {
                'title': 'Расписание на следующую неделю',
                'content': 'Уважаемые менторы! Просьба подтвердить расписание занятий на следующую неделю в системе.',
                'audience': 'mentors',
                'is_published': True,
                'created_by': admin_user,
            },
            {
                'title': 'Новые курсы в сентябре',
                'content': 'В сентябре мы запускаем два новых курса: Data Science и Mobile Development. Принимаем заявки от студентов.',
                'audience': 'all',
                'is_published': True,
                'created_by': admin_user,
            },
        ]

        for data in news_data:
            News.objects.get_or_create(title=data['title'], defaults=data)

    def _create_lectures(self, courses):
        from apps.lectures.models import Section, Material

        for course in courses[:2]:
            sections_data = [
                {'title': 'Введение', 'order': 1},
                {'title': 'Основы', 'order': 2},
                {'title': 'Продвинутый уровень', 'order': 3},
            ]
            for sec_data in sections_data:
                section, _ = Section.objects.get_or_create(
                    course=course,
                    title=sec_data['title'],
                    defaults={'order': sec_data['order']}
                )

                Material.objects.get_or_create(
                    section=section,
                    title=f'{sec_data["title"]} — Теория',
                    defaults={
                        'type': 'text',
                        'body_html': f'<p>Теоретический материал по теме «{sec_data["title"]}» для курса {course.title}.</p>',
                        'order': 1,
                    }
                )
                Material.objects.get_or_create(
                    section=section,
                    title=f'{sec_data["title"]} — Видео',
                    defaults={
                        'type': 'video',
                        'video_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                        'order': 2,
                    }
                )

    def _create_assignments(self, courses):
        from apps.assignments.models import Assignment, AssignmentSubmission
        from apps.courses.models import CourseStudent

        for course in courses[:2]:
            for i in range(1, 4):
                assignment, _ = Assignment.objects.get_or_create(
                    course=course,
                    title=f'Задание {i} — {course.title}',
                    defaults={
                        'description': f'Описание задания {i}. Выполните все пункты и сдайте до дедлайна.',
                        'max_score': 100,
                        'due_date': date.today() + timedelta(days=i * 7),
                    }
                )

                enrolled = CourseStudent.objects.filter(course=course).select_related('student')
                for cs in list(enrolled)[:4]:
                    if random.choice([True, True, False]):
                        AssignmentSubmission.objects.get_or_create(
                            assignment=assignment,
                            student=cs.student,
                            defaults={
                                'answer_text': 'Решение задания приложено ниже.',
                                'submitted_at': timezone.now() - timedelta(days=random.randint(1, 5)),
                                'status': 'submitted',
                            }
                        )

    def _create_reviews(self, courses, admin_user):
        from apps.reviews.models import Review
        from apps.courses.models import CourseStudent

        comments = [
            'Отличный курс, всё понятно объяснено!',
            'Очень полезный материал, рекомендую.',
            'Ментор всегда на связи и помогает.',
            'Практические задания очень полезны.',
            'Хороший курс, но хотелось бы больше практики.',
        ]

        for course in courses[:2]:
            enrolled = CourseStudent.objects.filter(course=course).select_related('student')
            for cs in list(enrolled)[:3]:
                Review.objects.get_or_create(
                    course=course,
                    student=cs.student,
                    author=admin_user,
                    defaults={
                        'type': 'course_review',
                        'content': random.choice(comments),
                        'rating': random.randint(4, 5),
                    }
                )
