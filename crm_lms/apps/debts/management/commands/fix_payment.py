from django.core.management.base import BaseCommand
from apps.payments.models import Payment
from apps.students.models import Student
from apps.courses.models import Course
from apps.courses.models import CourseStudent
from apps.debts.models import Debt
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fix payment and test debt logic'

    def handle(self, *args, **options):
        self.stdout.write('=== Fixing payment and testing debt logic ===')

        # Get the student and course
        student = Student.objects.filter(full_name__contains='Adminova').first()
        course = Course.objects.filter(title__contains='chteni').first()

        self.stdout.write(f'Student: {student.full_name if student else "Not found"}')
        self.stdout.write(f'Course: {course.title if course else "Not found"}')

        if student and course:
            # Update existing payment
            payment = Payment.objects.filter(student=student, course=course).first()
            if payment:
                payment.amount = 1000.00
                payment.save()
                self.stdout.write(f'Updated payment: {payment.amount}, months: {payment.months_paid}')
            else:
                self.stdout.write('No existing payment found')

            # Test debt logic
            today = timezone.now().date()
            self.stdout.write(f'Today: {today}')
            
            # Get enrollment
            enrollment = CourseStudent.objects.filter(student=student, course=course, status='active').first()
            if enrollment:
                self.stdout.write(f'Enrollment found: {enrollment}')
                
                # Check payments with amount > 0
                payments = Payment.objects.filter(student=student, course=course, amount__gt=0)
                self.stdout.write(f'Payments with amount > 0: {payments.count()}')
                for p in payments:
                    self.stdout.write(f'  Amount: {p.amount}, Months: {p.months_paid}, Date: {p.paid_at}')
                
                # Test our method
                debt_manager = Debt.objects
                paid_months = debt_manager._get_paid_months_with_years(student, course)
                self.stdout.write(f'Paid months (year, month): {paid_months}')
                
                # Check if should be debtor
                is_debtor = debt_manager._is_student_debtor(enrollment, today)
                self.stdout.write(f'Is debtor: {is_debtor}')
                
                # Check start date
                start_date = enrollment.joined_at or course.start_date
                self.stdout.write(f'Start date: {start_date}')
                
                # Check current month
                current_month_tuple = (today.year, today.month)
                self.stdout.write(f'Current month {current_month_tuple} in paid months: {current_month_tuple in paid_months}')

        self.stdout.write('\n=== Running update debtors ===')
        result = Debt.objects.get_debtors()
        self.stdout.write(f'Debtors found: {len(result)}')
        for r in result:
            self.stdout.write(f'  - {r.student.full_name} ({r.course.title})')
