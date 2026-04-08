import os
import sys
import django

# Add the project path
sys.path.append('c:\\Users\\Admin\\Desktop\\OkuuTrack\\crm_lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from apps.payments.models import Payment
from apps.students.models import Student
from apps.courses.models import Course
from apps.courses.models import CourseStudent
from apps.debts.models import Debt
from django.utils import timezone

print('=== Fixing payment and testing debt logic ===')

# Get the student and course
student = Student.objects.filter(full_name__contains='Adminova').first()
course = Course.objects.filter(title__contains='chteni').first()

print(f'Student: {student.full_name if student else "Not found"}')
print(f'Course: {course.title if course else "Not found"}')

if student and course:
    # Update existing payment
    payment = Payment.objects.filter(student=student, course=course).first()
    if payment:
        payment.amount = 1000.00
        payment.save()
        print(f'Updated payment: {payment.amount}, months: {payment.months_paid}')
    else:
        print('No existing payment found')

    # Test debt logic
    today = timezone.now().date()
    print(f'Today: {today}')
    
    # Get enrollment
    enrollment = CourseStudent.objects.filter(student=student, course=course, status='active').first()
    if enrollment:
        print(f'Enrollment found: {enrollment}')
        
        # Check payments with amount > 0
        payments = Payment.objects.filter(student=student, course=course, amount__gt=0)
        print(f'Payments with amount > 0: {payments.count()}')
        for p in payments:
            print(f'  Amount: {p.amount}, Months: {p.months_paid}, Date: {p.paid_at}')
        
        # Test our method
        debt_manager = Debt.objects
        paid_months = debt_manager._get_paid_months_with_years(student, course)
        print(f'Paid months (year, month): {paid_months}')
        
        # Check if should be debtor
        is_debtor = debt_manager._is_student_debtor(enrollment, today)
        print(f'Is debtor: {is_debtor}')
        
        # Check start date
        start_date = enrollment.joined_at or course.start_date
        print(f'Start date: {start_date}')
        
        # Check current month
        current_month_tuple = (today.year, today.month)
        print(f'Current month {current_month_tuple} in paid months: {current_month_tuple in paid_months}')

print('\n=== Running update debtors ===')
result = Debt.objects.get_debtors()
print(f'Debtors found: {len(result)}')
for r in result:
    print(f'  - {r.student.full_name} ({r.course.title})')
