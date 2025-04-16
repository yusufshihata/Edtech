from django import forms
from django.utils import timezone
from .models import Course

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
