from django import forms
from django.core.exceptions import ValidationError

class BaseForm(forms.Form):
    """
    A reusable base form class for Django model operations with context-aware validation and saving.

    Provides common functionality for handling model instances, context variables, and unique
    validation checks. Designed to be subclassed for specific model forms.

    Subclasses Must Define:
        model (Model): The Django model class this form operates on.
        required_context (list): Context variables required for form operation (e.g., ['user', 'Skill']).
        context_to_field_map (dict): Mapping from context variable names to model field names
                                    (e.g., {'user': 'Learner'}).

    Key Features:
        1. Context Handling:
            - Requires predefined context variables passed as keyword arguments during initialization
            - Automatically validates presence of required context variables
            - Maps context values to model fields during save operations

        2. Model Operations:
            - Supports both create and update operations
            - Handles model instance initialization and updating
            - Built-in unique validation helper

    Methods:
        _validate_unique: Validates uniqueness of field values against model constraints
        save: Persists form data to model instance, incorporating context values

    Usage Example:
        class SkillForm(BaseForm):
            model = Skill
            required_context = ['user']
            context_to_field_map = {'user': 'Learner'}
            # ... form fields and custom validation ...

        # In view:
        form = SkillForm(data=request.data, user=request.user)
        if form.is_valid():
            instance = form.save()

    Notes:
        - Context variables are automatically removed from kwargs during initialization
        - Combines form data with context values during save() for complete model population
        - Maintains existing instance when updating (pass 'instance' kwarg)
    """
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

