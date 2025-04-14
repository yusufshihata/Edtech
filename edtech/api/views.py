from django.shortcuts import render
from rest_framework import status, permissions
from django.contrib.auth import login, logout
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import Student, Course, Unit, Task
from .serializer import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer

# Create your views here.
@api_view(['GET'])
def get_courses(render):
    courses = Course.objects.all()
    courses = CourseSerializer(courses, many=True)
    data = courses.data

    return Response(data)

@api_view(['GET'])
def get_course_by_id(render, course_id):
    course = Course.objects.get(id=course_id)
    course = CourseSerializer(course)

    data = course.data
    return Response(data)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            user_data = StudentSerializer(user).data
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            user_data = StudentSerializer(user).data
            return Response(user_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'details': 'Successfully logged out.'}, status=status.HTTP_200_OK)

class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = StudentSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

