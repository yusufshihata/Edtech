from django.urls import path
from . import views

urlpatterns = [
    path('Skills', views.SkillsListView.as_view(), name="Skills"),
    path('Skills/<int:Skill_id>/', views.SkillDetailView.as_view(), name='Skill-details'),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('Learner/', views.UserDetailView.as_view(), name='user-detail'),
    path('Skills/<int:Skill_id>/units/', views.UnitsListView.as_view(), name='units'),
    path('Skills/<int:Skill_id>/units/<int:unit_id>/', views.UnitDetailView.as_view(), name='unit-detail'),
    path('Skills/<int:Skill_id>/units/<int:unit_id>/tasks/', views.TasksListView.as_view(), name='tasks'),
    path('Skills/<int:Skill_id>/units/<int:unit_id>/tasks/<int:task_id>/', views.TaskDetailView.as_view(), name='task-details')
]

