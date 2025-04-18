from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Course, Unit, Task

class BaseForm(forms.Form):
    """Base form with common functionality for context handling and validation"""
    required_context = []

    def __init__(self, *args, **kwargs):
        self.context = {var: kwargs.pop(var, None) for var in self.required_context}
        super().__init__(*args, **kwargs)
        self._validate_context()
    
    def _validate_context(self):
        """Helper method to ensure that context variables are present"""
        for var in self.required_context:
            if self.context.get(var) is None:
                raise ValueError(f"Messing Required context variable: {var}")

    def _validate_unique(self, model, filters, error_message, field=None):
        """Helper method for unique validation"""
        if model.objects.filter(**filters).exists():
            error = ValidationError(error_message)
            if field:
                self.add_error(field, error)
            else:
                raise error

class CourseForm(BaseForm):
    required_context = ['user']
    name = forms.CharField(max_length=100)
    mid_deadline = forms.DateField()
    final_deadline = forms.DateField()

    def _validate_deadlines(self, mid, final):
        """Helper method to validate the deadlines of the coures"""
        if final <= timezone.now().date():
            self.add_error("final_deadline", "Deadline must be in the future.")
        if final < mid:
            self.add_error("mid_deadline", "Midterm deadline must be before final exam deadline.")


    def clean(self):
        cleaned_data = super().clean()
        student = self.context['user']

        mid = cleaned_data.get('mid_deadline')
        final = cleaned_data.get('final_deadline')

        # Deadline Logic Validation
        self._validate_deadlines(mid, final)
        
        # Unique Course validation
        self._validate_unique(
            model=Course,
            filters={'name': cleaned_data.get('name'), 'student': student},
            error_message=f"You Already have a course named {cleaned_data.get('name')}",
            field='name'
        )

        return cleaned_data


class UnitForm(BaseForm):
    required_context = ['user', 'course']
    title = forms.CharField(max_length=100)

    def clean(self):
        cleaned_data = super().clean()
        student = self.context['user']
        course = self.context['course']

        # User Authorization Check
        if course.student != student:
            self.add_error(None, "You're not Authorized to perform this operation.")

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
    required_context = ['user', 'course', 'unit']
    title = forms.CharField(max_length=100)
    deadline = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        student = self.context['user']
        course = self.context['course']
        unit = self.context['unit']

        # User Authorization Check
        if course.student != student:
            self.add_error(None, "You're not Authroized to perform this operation.")

        # Unique task validation
        self.validate_unique(
            model=Task,
            filters={'title': cleaned_data.get('title'), 'unit': unit},
            error_message=f"Task '{cleaned_data.get('title')}' already exists in this unit",
            field='title'
        )

        return cleaned_data