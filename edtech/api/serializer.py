from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student, Unit, Course, Task

class StudentSerializer(serializers.ModelSerializer):
    birth_date = serializers.DateField(source='student.birth_date', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'birth_date')
        read_only_fields = ('id',) 

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['title']


class CourseSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    student = StudentSerializer(many=False, read_only=True)
    class Meta:
        model = Course
        fields = ['name', 'mid_deadline', 'final_deadline', 'units', 'student']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password", style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    birth_date = serializers.DateField(required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email address already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        birth_date = validated_data.pop('birth_date')

        validated_data.pop('password2')

        password = validated_data.pop('password')

        user = User.objects.create_user(password=password, **validated_data)

        try:
            Student.objects.create(user=user, birth_date=birth_date)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create student profile: {e}")

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)

            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "username" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
