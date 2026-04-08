from apps.students.models import Student
from apps.courses.models import CourseStudent

print("=== Проверка студентов и их курсов ===")

# Показываем всех студентов
students = Student.objects.all()[:5]
for student in students:
    print(f"\nСтудент: {student.full_name} (ID: {student.id})")
    
    # Показываем курсы студента
    course_students = CourseStudent.objects.filter(student=student)
    print(f"  Всего записей на курсы: {course_students.count()}")
    
    for cs in course_students:
        print(f"  - Курс: {cs.course.title} (статус: {cs.status})")
        
    # Показываем только активные
    active_courses = CourseStudent.objects.filter(student=student, status='active')
    print(f"  Активных курсов: {active_courses.count()}")

print("\n=== Проверка завершена ===")
