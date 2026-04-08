from django.urls import path

# Временная заглушка для теста
def dummy_view(request, course_id, lesson_id):
    from django.http import HttpResponse
    return HttpResponse(f"Substitute view for course {course_id}, lesson {lesson_id}")

app_name = 'lessons_substitute'

urlpatterns = [
    path('courses/<int:course_id>/lessons/<int:lesson_id>/substitute/', dummy_view, name='substitute_mentor'),
    # path('courses/<int:course_id>/lessons/<int:lesson_id>/substitute/create/', views_substitute.create_substitution, name='create_substitution'),
    # path('substitutions/<int:substitution_id>/confirm/', views_substitute.confirm_substitution, name='confirm_substitution'),
    # path('substitutions/<int:substitution_id>/cancel/', views_substitute.cancel_substitution, name='cancel_substitution'),
]
