from django import forms
from django.utils import timezone
from core.base_forms import BaseForm
from .models import Course, Unit, Task

class CourseForm(BaseForm):
    required_context = ['user']
    model = Course
    context_to_field_map = {'user': 'student'}
    
    name = forms.CharField(max_length=100)
    mid_deadline = forms.DateField()
    final_deadline = forms.DateField()

    def _validate_deadlines(self, mid, final):
        """Logic validation of the deadlines"""
        if final <= timezone.now().date():
            self.add_error("final_deadline", "Deadline must be in the future.")
        if final < mid:
            self.add_error("mid_deadline", "Midterm deadline must be before final exam deadline.")

    def clean(self):
        cleaned_data = super().clean()
        student = self.context['user']

        mid = cleaned_data.get('mid_deadline')
        final = cleaned_data.get('final_deadline')

        # Validate if the deadlines are logically set
        self._validate_deadlines(mid, final)
        
        # Validate if the course is unique for this user
        self._validate_unique(
            model=Course,
            filters={'name': cleaned_data.get('name'), 'student': student},
            error_message=f"You already have a course named {cleaned_data.get('name')}",
            field='name'
        )

        return cleaned_data

class UnitForm(BaseForm):
    required_context = ['course']
    model = Unit
    title = forms.CharField(max_length=100)
    context_to_field_map = {'course': 'course'}

    def clean(self):
        cleaned_data = super().clean()
        course = self.context['course']

        # Validate deadline if provided
        if deadline := cleaned_data.get('deadline'):
            if deadline <= timezone.now().date():
                self.add_error('deadline', "Deadline must be in the future")
        
        # Unique Unit validation
        self._validate_unique(
            model=Unit,
            filters={'title': cleaned_data.get('title'), 'course': course},
            error_message=f"Unit {cleaned_data.get('title')} already exists in this course.",
            field='title'
        )

        return cleaned_data

class TaskForm(BaseForm):
    model = Task
    required_context = ['unit', 'course']
    context_to_field_map = {'course': 'course', 'unit': 'unit'}
    
    title = forms.CharField(max_length=100)
    deadline = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        unit = self.context['unit']

        # Unique task validation
        self._validate_unique(
            model=Task,
            filters={'title': cleaned_data.get('title'), 'unit': unit},
            error_message=f"Task '{cleaned_data.get('title')}' already exists in this unit",
            field='title'
        )

        return cleaned_data
