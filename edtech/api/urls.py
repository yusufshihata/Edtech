from django.urls import path
from . import views

urlpatterns = [
    path('courses', views.CoursesListView.as_view(), name="courses"),
    path('courses/<int:course_id>/', views.CourseDetailView.as_view(), name='course-details'),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('student/', views.UserDetailView.as_view(), name='user-detail'),
    path('courses/<int:course_id>/units/', views.UnitsListView.as_view(), name='units'),
    path('courses/<int:course_id>/units/<int:unit_id>/', views.UnitDetailView.as_view(), name='unit-detail'),
    path('courses/<int:course_id>/units/<int:unit_id>/tasks/', views.TasksListView.as_view(), name='tasks'),
    path('courses/<int:course_id>/units/<int:unit_id>/tasks/<int:task_id>/', views.TaskDetailView.as_view(), name='task-details')
]

