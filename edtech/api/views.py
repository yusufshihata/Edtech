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
from .serializer import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer, UnitSerializer, TaskSerializer
from .forms import CourseForm, UnitForm, TaskForm
from django.shortcuts import get_object_or_404

# Create your views here.
class CoursesListView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.filter(student=request.user)
        courses = CourseSerializer(courses, many=True)
        data = courses.data

        return Response(data)

    def post(self, request):
        student = request.user
        form = CourseForm(request.data, user=student)

        if form.is_valid():
            name = form.cleaned_data['name']
            mid_deadline = form.cleaned_data['mid_deadline']
            final_deadline = form.cleaned_data['final_deadline']

            course = Course.objects.create(
                student=student,
                name=name,
                mid_deadline=mid_deadline,
                final_deadline=final_deadline
            )

            course = CourseSerializer(course)

            return Response(course.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        course = CourseSerializer(course)
        data = course.data
        return Response(data)

    def patch(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)

        serializer = CourseSerializer(
            instance=course,
            data=request.data,
            partial=True,
            context={'request':request}
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    def delete(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        course.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class UnitsListView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        units = Unit.objects.filter(course=course)
        units = UnitSerializer(units, many=True)
        data = units.data

        return Response(data)
    
    def post(self, request, course_id):
        student = request.user
        course = Course.objects.get(id=course_id)
        form = UnitForm(request.data, user=student, course=course)

        if form.is_valid():
            title = form.cleaned_data['title']

            unit = Unit.objects.create(
                title=title,
                course=course
            )

            unit = UnitSerializer(unit)

            return Response(unit.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, unit_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        unit = get_object_or_404(Unit, course=course, id=unit_id)
        unit = UnitSerializer(unit)

        return Response(unit.data)

    def patch(self, request, course_id, unit_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        unit = get_object_or_404(Unit, id=unit_id, course=course)

        serializer = UnitSerializer(
            instance=unit,
            data=request.data,
            partial=True,
            context={'request':request}
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)



    def delete(self, request, course_id, unit_id):
        unit = get_object_or_404(Unit, id=unit_id)
        unit.delete()

        return Response({"context": "Unit deleted successfully"})

class TasksListView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, unit_id):
        course = get_object_or_404(Course, id=course_id, student=request.user)
        unit = get_object_or_404(Unit, id=unit_id, course=course)
        tasks = Task.objects.filter(unit=unit)
        tasks = TaskSerializer(tasks, many=True)
        data = tasks.data

        return Response(data)

    def post(self, request, course_id, unit_id):
        student = request.user
        course = get_object_or_404(Course, id=course_id, student=student)
        unit = get_object_or_404(Unit, id=unit_id, course=course)
        form = TaskForm(request.data, course=course, unit=unit)

        if form.is_valid():
            title = form.cleaned_data['title']
            deadline = form.cleaned_data['deadline']
            done = False

            task = Task.objects.create(
                title=title,
                deadline=deadline,
                done=done,
                course=course,
                unit=unit
            )

            task = TaskSerializer(task)

            return Response(task.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskDetailView(APIView):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, unit_id, task_id):
        student = request.user
        course = get_object_or_404(Course, id=course_id, student=student)
        unit = get_object_or_404(Unit, id=unit_id, course=course)
        task = Task.objects.get(id=task_id, unit=unit)
        task = TaskSerializer(task)
        return Response(task.data)

    def patch(self, request, course_id, unit_id, task_id):
        student = request.user
        course = get_object_or_404(Course, id=course_id, student=student)
        unit = get_object_or_404(Unit, id=unit_id, course=course)
        task = Task.objects.get(id=task_id, unit=unit)

        serializer = TaskSerializer(
            instance=task,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)

    def delete(self, request, course_id, unit_id, task_id):
        student = request.user
        course = get_object_or_404(Course, id=course_id, student=student)
        unit = get_object_or_404(Unit, id=unit_id, course=course)
        task = Task.objects.get(id=task_id, unit=unit)
        task.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

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

