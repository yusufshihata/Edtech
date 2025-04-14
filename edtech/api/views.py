from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import Student, Course, Unit, Task
from .serializer import CourseSerializer

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
