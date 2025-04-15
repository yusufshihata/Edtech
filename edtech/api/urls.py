from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path('courses', views.CoursesListView.as_view(), name="courses"),
    path('courses/<int:course_id>/', views.get_course_by_id, name='course-details'),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('student/', views.UserDetailView.as_view(), name='user-detail'),
    path('api-token-auth/', obtain_auth_token),
]

