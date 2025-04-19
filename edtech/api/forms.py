from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Course, Unit, Task

class BaseForm(forms.Form):
    """Base form with common functionality for context handling and validation"""
    required_context = []
    model = None
    context_to_field_map = {}  # Corrected spelling

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.context = {var: kwargs.pop(var, None) for var in self.required_context}
        data = kwargs.pop('data', None)
        if data is None and args:
            data = args[0]
            args = args[1:]
        initial = kwargs.pop('initial', None)
        if self.instance and initial is None:
            initial = forms.models.model_to_dict(self.instance)
        
        super().__init__(data=data, initial=initial, *args, **kwargs)
        self._validate_context()

    def _validate_context(self):
        """Helper method to ensure that context variables are present"""
        for var in self.required_context:
            if self.context.get(var) is None:
                raise ValueError(f"Missing required context variable: {var}")

    # The rest of the methods remain unchanged
    def _validate_unique(self, model, filters, error_message, field=None, exclude_instance=True):
        """Helper method for unique validation"""
        queryset = model.objects.filter(**filters)
        if self.instance and self.instance.pk and exclude_instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            error = ValidationError(error_message)
            if field:
                self.add_error(field, error)
            else:
                self.add_error(None, error)

    def is_valid(self):
        return super().is_valid()
    
    def save(self, commit=True):
        if not self.model:
            raise TypeError("Subclass must define a model.")
        if not hasattr(self, 'cleaned_data'):
            raise ValueError("Form not validated")

        data_to_save = self.cleaned_data.copy()

        # Map context variables to model fields
        for context_key, model_field in self.context_to_field_map.items():
            if context_key in self.context:
                data_to_save[model_field] = self.context[context_key]

        if self.instance and self.instance.pk:
            # Update existing instance
            for field, value in data_to_save.items():
                setattr(self.instance, field, value)
            instance = self.instance
        else:
            # Create new instance with context variables
            instance = self.model(**data_to_save)
            self.instance = instance

        if commit:
            instance.save()
        return instance

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
    required_context = ['user', 'course']
    title = forms.CharField(max_length=100)
    context_to_field_map = {'user': 'student', 'course': 'course'}

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
    context_to_field_map = {'user': 'student', 'course': 'course', 'unit': 'unit'}
    
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
        self._validate_unique(
            model=Task,
            filters={'title': cleaned_data.get('title'), 'unit': unit},
            error_message=f"Task '{cleaned_data.get('title')}' already exists in this unit",
            field='title'
        )

        return cleaned_data
