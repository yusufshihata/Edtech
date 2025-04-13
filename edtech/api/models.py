from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import PROTECT
from django.utils import timezone

# Create your models here.
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    birth_date = models.DateField()

    def __str__(self):
        return self.user.username

class Course(models.Model):
    name = models.CharField(max_length=100)
    mid_deadline = models.DateField()
    final_deadline = models.DateField()
    student = models.ForeignKey(User, on_delete=models.PROTECT)

class Unit(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)


class Task(models.Model):
    title = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    deadline = models.DateField(default=timezone.now)
    done = models.BooleanField(default=False)


