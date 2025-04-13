from django.contrib import admin
from .models import Student, Course, Unit, Task

# Register your models here.
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Unit)
admin.site.register(Task)
