from django.shortcuts import render, redirect
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import login, logout
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import Student, Course, Unit, Task
from .serializers import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer, UnitSerializer, TaskSerializer
from .forms import CourseForm, UnitForm, TaskForm
from django.shortcuts import get_object_or_404

class BaseListView(APIView):
    """Base Class for the List Views in the API"""
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    form_class = None
    parent_models = []

    def get_queryset(self, request, *args, **kwargs):
        """Get the queryset filtered by user"""
        return self.model.objects.filter(student=request.user)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request, *args, **kwargs)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.data, user=request.user, **self.get_form_context())
        if form.is_valid():
            instance = form.save()
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_form_context(self):
        """Get additional context for form initialization"""
        context = {}
        for param, model in self.parent_models:
            obj = get_object_or_404(model, id=self.kwargs.get(f'{param}_id'), student=self.request.user)
            context[param] = obj
        return context

class BaseDetailView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    related_models = []

    def get_object(self, **filters):
        """Get object with permission check"""
        # Handle nested relationships
        query_filters = {'student': self.request.user}
        for relation in self.related_models:
            param = f'{relation}_id'
            model = globals()[relation.capitalize()]
            query_filters[relation] = get_object_or_404(model, id=self.kwargs.get(param))
        
        query_filters.update(filters)
        return get_object_or_404(self.model, **query_filters)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(
            instance=instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CoursesListView(BaseListView):
    model = Course
    serializer_class = CourseSerializer
    form_class = CourseForm

class CourseDetailView(BaseDetailView):
    model = Course
    serializer_class = CourseSerializer

class UnitsListView(BaseListView):
    model = Unit
    serializer_class = UnitSerializer
    form_class = UnitForm
    parent_models = [('course', Course)]

    def get_queryset(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=kwargs.get('course_id'), student=request.user)
        return Unit.objects.filter(course=course)

class UnitDetailView(BaseDetailView):
    model = Unit
    serializer_class = UnitSerializer
    related_models = ['course']

class TasksListView(BaseListView):
    model = Task
    serializer_class = TaskSerializer
    form_class = TaskForm
    parent_models = [('course', Course), ('unit', Unit)]

    def get_queryset(self, request, *args, **kwargs):
        unit = get_object_or_404(Unit, id=kwargs.get('unit_id'), course__student=request.user)
        return Task.objects.filter(unit=unit)

class TaskDetailView(BaseDetailView):
    model = Task
    serializer_class = TaskSerializer
    related_models = ['course', 'unit']


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

