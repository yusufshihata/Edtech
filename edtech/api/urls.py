from django.urls import path
from . import views

urlpatterns = [
    path('courses', views.get_courses),
    path('courses/<int:course_id>/', views.get_course_by_id, name='course-details'),
]

