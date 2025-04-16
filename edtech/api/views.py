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
from .serializer import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer
from .forms import CourseForm

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
        try:
            course = Course.objects.get(id=course_id, student=request.user)
        except:
            raise ValueError("this is not your course")
        course = CourseSerializer(course)
        data = course.data
        return Response(data)

    def delete(self, request):
        pass

@api_view(['GET'])
def get_course_by_id(render, course_id):
    course = Course.objects.get(id=course_id)
    course = CourseSerializer(course)

    data = course.data
    return Response(data)

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

