from django import forms
from django.utils import timezone
from .models import Course, Unit, Task

class CourseForm(forms.Form):
    name = forms.CharField(max_length=100)
    mid_deadline = forms.DateField()
    final_deadline = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not self.student:
            raise ValueError("Not Authorized to do this operation.")

    def clean(self):
        cleaned_data = super().clean()
        student = self.student

        mid_deadline = cleaned_data.get('mid_deadline')
        final_deadline = cleaned_data.get('final_deadline')

        if final_deadline <= timezone.now():
            raise forms.ValidationError({"final_deadline": "final exam must be in the future"})

        if mid_deadline >= final_deadline:
            raise forms.ValidationError({"mid_deadline": "Midterm deadline must be before final exam deadline."})

        if Course.objects.filter(name=cleaned_data.get('name'), student=student).exists():
            raise forms.ValidationError({"duplication": f"You already have a course with the name {cleaned_data.get('name')}"})

class UnitForm(forms.Form):
    title = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('user', None)
        self.course = kwargs.pop('course', None)

        super().__init__(*args, **kwargs)

        if not self.course:
            raise ValueError({"course": "can't find a course"})

        if self.course.student != self.student:
            raise ValueError({"auth_error": "can't find authentication tokens"})

    def clean(self):
        cleaned_data = super().clean()
        student = self.student
        course = self.course

        if Unit.objects.filter(title=cleaned_data.get('title'), course=course).exists():
            raise forms.ValidationError(f"You already have a course with the name {cleaned_data.get('title')}")

        if not Course.objects.filter(name=course.name, student=student).exists():
            raise forms.ValidationError({"authorization": "You're not authorized to do this."})

class TaskForm(forms.Form):
    title = forms.CharField(max_length=100)
    deadline = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        self.unit = kwargs.pop('unit', None)

        super().__init__(*args, **kwargs)

        if not (self.course and self.unit):
            raise ValueError("There is no course or unit in here.")

    def clean(self):
        cleaned_data = super().clean()
        unit = self.unit

        if Task.objects.filter(title=cleaned_data.get('title'), unit=unit).exists():
            raise forms.ValidationError(f"You already have a task with the name {cleaned_data.get('title')}")

