from django.shortcuts import render, redirect
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import login, logout
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import Student, Course, Unit, Task
from .serializers import CourseSerializer, LoginSerializer, RegisterSerializer, StudentSerializer, UnitSerializer, TaskSerializer
from .forms import CourseForm, UnitForm, TaskForm
from django.shortcuts import get_object_or_404
from django.core.exceptions import ImproperlyConfigured

class BaseListView(APIView):
    """
    Base API view for listing multiple instances and creating new ones.

    Handles GET requests to list resources and POST requests to create a new resource.

    List Filtering:
    - The base `get_queryset` method filters instances by `student=request.user`.
      This assumes the model has a `student` field linked to the user.
    - For nested resources (defined in `parent_models`), subclasses should
      override `get_queryset` to further filter the results based on the
      parent objects found using URL keyword arguments like `{param_name}_id`.

    Creation (`POST`):
    - Uses the specified `form_class` for data validation and saving new instances.
    - Automatically passes `request.user` to the form's `__init__` method.
    - If `parent_models` are defined, it fetches the parent objects based on
      URL kwargs (`{param_name}_id`) using `get_form_context` and passes
      them as keyword arguments to the form's `__init__` method.
      Parent objects fetched this way are also filtered by `student=request.user`.

    Nested Resources:
    - Supported via the `parent_models` attribute: a list of tuples
      `(param_name, ParentModel)`, e.g., `[('course', Course)]`.
    - The view expects corresponding URL keyword arguments like `{param_name}_id`
      (e.g., `course_id`) in `self.kwargs` to identify parent instances.

    Subclasses must define:
    - `model`: The Django model class this view operates on.
    - `serializer_class`: The DRF serializer class used for representing model instances.
                          Used in GET (with `many=True`) and POST (for the created instance).
    - `form_class`: The Django Form class used for validating input and creating
                    new model instances during POST requests.

    Optional Attributes:
    - `parent_models`: List of tuples `(param_name, ParentModel)` for handling
                       nested resources.

    Authentication & Permissions:
    - Defaults use `SessionAuthentication` and `BasicAuthentication`.
    - Default permission requires the user to be authenticated (`IsAuthenticated`).
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    form_class = None
    parent_models = []

    def get_queryset(self, request, *args, **kwargs):
        """Get the queryset filtered by user"""
        return self.model.objects.filter(student=request.user)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request, *args, **kwargs)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.data, user=request.user, **self.get_form_context())
        if form.is_valid():
            instance = form.save()
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_form_context(self):
        """Get additional context for form initialization"""
        context = {}
        for param, model in self.parent_models:
            obj = get_object_or_404(model, id=self.kwargs.get(f'{param}_id'), student=self.request.user)
            context[param] = obj
        return context

class BaseDetailView(APIView):
    """
    Base API view for single-instance operations (Retrieve, Update, Delete).

    Retrieves the instance using a URL keyword argument dynamically generated
    as `{model_name}_id` (e.g., `course_id` for a Course model).

    Subclasses must define:
    - `model`: The Django model class.
    - `serializer_class`: The DRF serializer class.
    - `parent_models` (optional): List of tuples `(param_name, ParentModel)` for nested resources.
                                   Example: [('course', Course)]
                                   Assumes parent lookup via `{param_name}_id`.
    - `lookup_field` (optional): The model field used for lookup in the database
                                  (default: 'id'). This is NOT the URL kwarg name anymore.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    parent_models = []
    lookup_field = 'id'

    def get_object(self):
        """
        Retrieve a single instance based on URL kwargs, using the convention
        `{model_name}_id` for the target instance's lookup key. Also handles
        nested resources and filters by the requesting user where appropriate.
        """
        if not self.model:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the 'model' attribute. "
                "It's required to determine the lookup URL keyword."
            )

        queryset = self.model.objects.all()

        model_name_lower = self.model.__name__.lower()
        instance_lookup_url_kwarg = f'{model_name_lower}_id'

        instance_lookup_value = self.kwargs.get(instance_lookup_url_kwarg)

        if instance_lookup_value is None:
            fallback_pk = self.kwargs.get('pk')
            fallback_id = self.kwargs.get('id')
            if fallback_pk or fallback_id:
                 raise Http404(
                     f"Expected URL keyword argument '{instance_lookup_url_kwarg}' not found. "
                     f"Found 'pk' or 'id' instead. Ensure your URL pattern uses '{instance_lookup_url_kwarg}'."
                 )
            else:
                 raise Http404(f"Expected URL keyword argument '{instance_lookup_url_kwarg}' not found in URLconf.")


        # --- Filter by Parent Objects (using {param_name}_id convention) ---
        parent_filters = {}
        for param_name, parent_model in self.parent_models:
            # Construct the expected URL kwarg for the parent ID, e.g., 'course_id'
            parent_lookup_url_kwarg = f'{param_name}_id'
            parent_id = self.kwargs.get(parent_lookup_url_kwarg)

            if parent_id is None:
                raise Http404(f"Expected URL keyword argument '{parent_lookup_url_kwarg}' for parent '{param_name}' not found.")

            # Fetch the parent object, ensuring the user owns it (if applicable)
            try:
                parent_qs = parent_model.objects
                parent_filter_kwargs = {'id': parent_id}
                if hasattr(parent_model, 'student'):
                    parent_filter_kwargs['student'] = self.request.user

                parent_obj = get_object_or_404(parent_qs, **parent_filter_kwargs)

            except Http404:
                 raise Http404(f"Parent {parent_model.__name__} with ID {parent_id} not found or not accessible by user.")
            except AttributeError as e:
                 # Handle cases where the model structure might be unexpected (e.g., 'student' field missing when expected)
                 print(f"Warning: AttributeError checking/accessing 'student' field on {parent_model.__name__}: {e}")
                 raise Http404(f"Configuration error accessing parent {parent_model.__name__}.")

            parent_filters[f'{param_name}'] = parent_obj

        filters = {
            self.lookup_field: instance_lookup_value,
            **parent_filters
        }

        if hasattr(self.model, 'student'):
             filters['student'] = self.request.user

        try:
            obj = get_object_or_404(queryset, **filters)
        except (TypeError, ValueError) as e:
            print(f"Error during object lookup: {e}")
            raise Http404(f"Invalid lookup parameters for {self.model.__name__} using filter {filters}.")

        self.check_object_permissions(self.request, obj)

        return obj

    def get(self, request, *args, **kwargs):
        """Retrieve a single instance."""
        instance = self.get_object()
        serializer = self.serializer_class(instance, context={'request': request})
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Update a single instance (full update)."""
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """Partially update a single instance."""
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """Delete a single instance."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CoursesListView(BaseListView):
    model = Course
    serializer_class = CourseSerializer
    form_class = CourseForm

class CourseDetailView(BaseDetailView):
    model = Course
    serializer_class = CourseSerializer

class UnitsListView(BaseListView):
    model = Unit
    serializer_class = UnitSerializer
    form_class = UnitForm
    parent_models = [('course', Course)]

    def get_queryset(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=kwargs.get('course_id'), student=request.user)
        return Unit.objects.filter(course=course)

class UnitDetailView(BaseDetailView):
    model = Unit
    serializer_class = UnitSerializer
    related_models = ['course']

class TasksListView(BaseListView):
    model = Task
    serializer_class = TaskSerializer
    form_class = TaskForm
    parent_models = [('course', Course), ('unit', Unit)]

    def get_queryset(self, request, *args, **kwargs):
        unit = get_object_or_404(Unit, id=kwargs.get('unit_id'), course__student=request.user)
        return Task.objects.filter(unit=unit)

class TaskDetailView(BaseDetailView):
    model = Task
    serializer_class = TaskSerializer
    related_models = ['course', 'unit']


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Render the registration form
        return render(request, 'register.html')
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Log the user in after registration
            login(request, user)
            
            # Redirect to user dashboard
            return redirect('user-detail')
        
        # If validation fails, render the form again with errors
        return render(request, 'register.html', {'errors': serializer.errors})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return redirect('user-detail')
        
        return render(request, 'login.html', {'errors': serializer.errors})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        logout(request)
        request.session.flush()
        response = redirect('login')
        response.delete_cookie('sessionid')
        return response



class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_data = StudentSerializer(request.user).data
        return render(request, 'user_detail.html', {'user': user_data})

