from django.urls import path
from . import views

urlpatterns = [
    path('courses', views.get_courses),
    path('courses/<int:course_id>/', views.get_course_by_id, name='course-details'),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('student/', views.UserDetailView.as_view(), name='user-detail')
]

