from django import forms
from django.utils import timezone
from core.base_forms import BaseForm
from .models import Skill, Unit, Task

class SkillForm(BaseForm):
    required_context = ['user']
    model = Skill
    context_to_field_map = {'user': 'Learner'}
    
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
        Learner = self.context['user']

        mid = cleaned_data.get('mid_deadline')
        final = cleaned_data.get('final_deadline')

        # Validate if the deadlines are logically set
        self._validate_deadlines(mid, final)
        
        # Validate if the Skill is unique for this user
        self._validate_unique(
            model=Skill,
            filters={'name': cleaned_data.get('name'), 'Learner': Learner},
            error_message=f"You already have a Skill named {cleaned_data.get('name')}",
            field='name'
        )

        return cleaned_data

class UnitForm(BaseForm):
    required_context = ['Skill']
    model = Unit
    title = forms.CharField(max_length=100)
    context_to_field_map = {'Skill': 'Skill'}

    def clean(self):
        cleaned_data = super().clean()
        Skill = self.context['Skill']

        # Validate deadline if provided
        if deadline := cleaned_data.get('deadline'):
            if deadline <= timezone.now().date():
                self.add_error('deadline', "Deadline must be in the future")
        
        # Unique Unit validation
        self._validate_unique(
            model=Unit,
            filters={'title': cleaned_data.get('title'), 'Skill': Skill},
            error_message=f"Unit {cleaned_data.get('title')} already exists in this Skill.",
            field='title'
        )

        return cleaned_data

class TaskForm(BaseForm):
    model = Task
    required_context = ['unit', 'Skill']
    context_to_field_map = {'Skill': 'Skill', 'unit': 'unit'}
    
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
