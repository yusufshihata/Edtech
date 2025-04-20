from django.shortcuts import render, redirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from rest_framework import permissions
from core.base_views import BaseListView, BaseDetailView
from .models import Course, Unit, Task
from .serializers import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer, UnitSerializer, TaskSerializer
from .forms import CourseForm, UnitForm, TaskForm

# List Views
class CoursesListView(BaseListView):
    model = Course
    serializer_class = CourseSerializer
    form_class = CourseForm

class UnitsListView(BaseListView):
    model = Unit
    serializer_class = UnitSerializer
    form_class = UnitForm
    parent_models = [('course', Course)]

    def get_queryset(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=kwargs.get('course_id'), student=request.user)
        return Unit.objects.filter(course=course)

class TasksListView(BaseListView):
    model = Task
    serializer_class = TaskSerializer
    form_class = TaskForm
    parent_models = [('course', Course), ('unit', Unit)]

    def get_queryset(self, request, *args, **kwargs):
            unit_id = kwargs.get('unit_id')
            course_id = kwargs.get('course_id')
            if unit_id is None or course_id is None:
                raise Http404("URL must contain course_id and unit_id.")

            unit = get_object_or_404(
                Unit,
                id=unit_id,
                course_id=course_id,
                course__student=request.user
            )
            return Task.objects.filter(unit=unit)

# Details Views
class CourseDetailView(BaseDetailView):
    model = Course
    serializer_class = CourseSerializer


    def get_queryset(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=kwargs.get('course_id'), student=request.user)
        return Unit.objects.filter(course=course)

class UnitDetailView(BaseDetailView):
    model = Unit
    serializer_class = UnitSerializer
    parent_models = [('course', Course)]

class TaskDetailView(BaseDetailView):
    model = Task
    serializer_class = TaskSerializer
    parent_models = [('course', Course), ('unit', Unit)]


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Render the registration form
        return render(request, 'register.html')
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Log the user in after registration
            login(request, user)
            
            # Redirect to user dashboard
            return redirect('user-detail')
        
        # If validation fails, render the form again with errors
        return render(request, 'register.html', {'errors': serializer.errors})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return redirect('user-detail')
        
        return render(request, 'login.html', {'errors': serializer.errors})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        logout(request)
        request.session.flush()
        response = redirect('login')
        response.delete_cookie('sessionid')
        return response



class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_data = StudentSerializer(request.user).data
        return render(request, 'user_detail.html', {'user': user_data})

