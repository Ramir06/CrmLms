#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from apps.payments.models import Payment
from apps.students.models import Student
from apps.courses.models import Course
from apps.courses.models import CourseStudent

print('=== Students ===')
for s in Student.objects.all():
    print(f'ID: {s.id}, Name: "{s.full_name}"')

print('\n=== Courses ===')
for c in Course.objects.all():
    print(f'ID: {c.id}, Title: "{c.title}"')

print('\n=== Course Students ===')
for cs in CourseStudent.objects.all():
    print(f'Student: "{cs.student.full_name}", Course: "{cs.course.title}"')

# Update Adminova's payment
student = Student.objects.filter(full_name__contains='Adminova').first()
course = Course.objects.filter(title__contains='chteni').first()

if student and course:
    payment = Payment.objects.filter(student=student, course=course).first()
    if payment:
        payment.amount = 1000.00
        payment.save()
        print(f'\nUpdated payment: {payment.amount}, months: {payment.months_paid}')
    else:
        print('\nNo payment found')
else:
    print('\nStudent or course not found')
