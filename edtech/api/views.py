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
from django.core.exceptions import ImproperlyConfigured, FieldDoesNotExist
import inspect

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
        """Get the queryset filtered by user. Assumes direct 'student' field.
           Subclasses for nested resources MUST override this."""
        if not hasattr(self.model, 'student'):
             raise ImproperlyConfigured(
                 f"{self.__class__.__name__} uses default get_queryset, but model "
                 f"{self.model.__name__} lacks 'student' field. Override get_queryset "
                 f"for nested resources like Units or Tasks."
             )
        return self.model.objects.filter(student=request.user)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request, *args, **kwargs)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        # Consider simplifying context handling if 'required_context' isn't strictly needed
        form_context = self.get_form_context(request, *args, **kwargs) # Pass request/kwargs

        # Add user if form expects it (check __init__ signature or a class attribute)
        # A common pattern is just to pass it if the form needs it.
        # Let's assume forms might need 'user' or specific parents.
        init_params = list(inspect.signature(self.form_class.__init__).parameters)
        if 'user' in init_params:
            form_context['user'] = request.user

        # Filter context to only what the form explicitly takes in __init__ ?
        # This prevents errors if extra context is passed, but standard forms ignore extras.
        # Keeping your original filtering logic based on required_context if you use that pattern:
        if hasattr(self.form_class, 'required_context'):
             filtered_context = {
                 key: value
                 for key, value in form_context.items()
                 if key in self.form_class.required_context
             }
        else:
            # Default: pass all context (parents, user if needed)
            # Filter to only keys expected by form's __init__ to be safe
            valid_keys = init_params[1:] # Skip 'self', take other args/kwargs
            filtered_context = {
                key: value for key, value in form_context.items() if key in valid_keys
            }


        form = self.form_class(request.data, **filtered_context)

        if form.is_valid():
            instance = form.save()
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_form_context(self, request, *args, **kwargs):
        """
        Get parent objects for form initialization, ensuring ownership chain.
        """
        context = {}
        parent_objects_so_far = {}

        for param_name, parent_model in self.parent_models:
            parent_lookup_url_kwarg = f'{param_name}_id'
            parent_id = kwargs.get(parent_lookup_url_kwarg)
            if parent_id is None:
                raise Http404(f"URL Configuration Error: Missing '{parent_lookup_url_kwarg}' in URL for POST request.")

            parent_qs = parent_model.objects
            current_parent_lookup_filters = {'id': parent_id}

            # Check relationship to previously fetched parents
            for prev_param, prev_model in self.parent_models:
                 if prev_param == param_name: break
                 try:
                     fk_field = parent_model._meta.get_field(prev_param)
                     if fk_field.is_relation and fk_field.remote_field.model == prev_model:
                          if prev_param in parent_objects_so_far:
                               current_parent_lookup_filters[prev_param] = parent_objects_so_far[prev_param].pk # Filter by PK
                          else:
                               raise ImproperlyConfigured(f"Cannot filter {parent_model.__name__} by {prev_param}: Previous parent not yet fetched.")
                 except FieldDoesNotExist: pass

            # Enforce 'student' ownership on the top-level parent
            if self.parent_models and param_name == self.parent_models[0][0]:
                 if hasattr(parent_model, 'student'):
                     current_parent_lookup_filters['student'] = request.user
                 else:
                     raise ImproperlyConfigured(f"Top-level parent {parent_model.__name__} in {self.__class__.__name__} requires a 'student' field for ownership check.")

            try:
                parent_obj = get_object_or_404(parent_qs, **current_parent_lookup_filters)
                context[param_name] = parent_obj
                parent_objects_so_far[param_name] = parent_obj
            except Http404:
                 raise Http404(
                     f"Not Found or Access Denied: Parent {parent_model.__name__} with query "
                     f"{current_parent_lookup_filters} not found for form context."
                 )
            except Exception as e:
                print(f"Error constructing filter for parent {parent_model.__name__} in get_form_context: {e}")
                raise Http404(f"Configuration error checking parent {parent_model.__name__} for form context.")

        return context


class BaseDetailView(APIView):
    """
    Base API view for single-instance operations (Retrieve, Update, Delete).

    Retrieves the instance using a URL keyword argument dynamically generated
    as `{model_name}_id` (e.g., `course_id` for a Course model).

    Ensures that nested resources (like Units, Tasks) are only retrieved if
    they belong to the specific parent instance(s) indicated in the URL,
    and that the top-level parent is owned by the requesting user.

    Subclasses must define:
    - `model`: The Django model class (e.g., Unit, Task).
    - `serializer_class`: The DRF serializer class.
    - `parent_models`: List of tuples `(param_name, ParentModel)` for nested resources.
                       Example: `[('course', Course)]` for UnitDetailView.
                       Example: `[('course', Course), ('unit', Unit)]` for TaskDetailView.
                       Assumes parent lookup via `{param_name}_id` in URL kwargs.
    - `lookup_field` (optional): The model field used for lookup in the database
                                  (default: 'id'). This is NOT the URL kwarg name.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    parent_models = []
    lookup_field = 'id'

    def get_object(self):
        """
        Retrieve a single instance, ensuring it belongs to the specified parents
        (retrieved via URL kwargs like `{parent_name}_id`) and that the ultimate
        parentage traces back to the requesting user.
        """
        if not self.model:
            raise ImproperlyConfigured(f"{self.__class__.__name__} is missing the 'model' attribute.")

        queryset = self.model.objects.all() # Start with all objects

        # --- Determine the lookup kwarg and value for the target instance ---
        model_name_lower = self.model.__name__.lower()
        instance_lookup_url_kwarg = f'{model_name_lower}_id'
        instance_lookup_value = self.kwargs.get(instance_lookup_url_kwarg)
        if instance_lookup_value is None:
            # Handle missing lookup value error as before
            fallback_pk = self.kwargs.get('pk')
            fallback_id = self.kwargs.get('id')
            expected_kwarg = f'<int:{instance_lookup_url_kwarg}>'
            if fallback_pk or fallback_id: raise Http404(...)
            else: raise Http404(...)

        # --- Build filters: Start with the target object's ID ---
        filters = {self.lookup_field: instance_lookup_value}

        # --- Fetch Parent Objects Sequentially and Add to Filters ---
        # This ensures ownership and relationship at each step
        fetched_parents_context = {} # Store {'course': <Course obj>} for filtering Unit

        for param_name, parent_model in self.parent_models:
            parent_lookup_url_kwarg = f'{param_name}_id'
            parent_id = self.kwargs.get(parent_lookup_url_kwarg)
            if parent_id is None:
                raise Http404(f"URL Config Error: Missing '{parent_lookup_url_kwarg}' for {parent_model.__name__}.")

            parent_qs = parent_model.objects
            current_parent_lookup_filters = {'id': parent_id}

            # --- Add relationship constraint to *previously* fetched parent ---
            for prev_param, prev_model in self.parent_models:
                if prev_param == param_name: break
                try:
                    fk_field = parent_model._meta.get_field(prev_param)
                    if fk_field.is_relation and fk_field.remote_field.model == prev_model:
                        if prev_param in fetched_parents_context:
                            # Filter by the actual parent object already validated
                            current_parent_lookup_filters[prev_param] = fetched_parents_context[prev_param]
                        else: raise ImproperlyConfigured(...)
                except FieldDoesNotExist: pass

            # --- Add ownership constraint if this is the top-level parent ---
            if self.parent_models and param_name == self.parent_models[0][0]:
                if hasattr(parent_model, 'student'):
                    current_parent_lookup_filters['student'] = self.request.user
                else: raise ImproperlyConfigured(...)

            try:
                # Fetch the parent securely
                parent_obj = get_object_or_404(parent_qs, **current_parent_lookup_filters)
                # Add the fetched parent object directly to the main filters for the target lookup
                filters[param_name] = parent_obj
                # Store context for the *next* parent lookup
                fetched_parents_context[param_name] = parent_obj
            except Http404:
                 raise Http404(f"Not Found/Access Denied: Parent {parent_model.__name__} query {current_parent_lookup_filters} failed.")
            except Exception as e:
                 print(f"Error fetching parent {parent_model.__name__} in get_object: {e}")
                 raise Http404(f"Config error accessing parent {parent_model.__name__}.")

        # --- Add Ownership Filter for Non-Nested Detail Views (e.g., CourseDetailView) ---
        # If there are no parents, check if the target model itself should be owned by the student
        if not self.parent_models and hasattr(self.model, 'student'):
            filters['student'] = self.request.user # Add the student filter directly

        # --- Retrieve the Target Object using combined filters ---
        try:
            # Example for TaskDetailView: Task.objects.get(id=task_id, unit=<Unit obj>, course=<Course obj>)
            # Example for CourseDetailView: Course.objects.get(id=course_id, student=request.user)
            obj = get_object_or_404(queryset, **filters)
        except Http404:
             denied_filters = {k:getattr(v, 'pk', v) for k,v in filters.items() if k != self.lookup_field}
             raise Http404(
                 f"Not Found/Access Denied: {self.model.__name__} with {self.lookup_field}={instance_lookup_value} "
                 f"matching criteria {denied_filters} not found."
             )
        except (FieldError, TypeError, ValueError) as e:
             print(f"Error during final lookup for {self.model.__name__}. Filters: {filters}. Error: {e}")
             raise Http404(f"Invalid lookup params/model field mismatch for {self.model.__name__}.")

        self.check_object_permissions(self.request, obj) # Standard DRF permissions
        return obj

    # --- get(), put(), patch(), delete() methods remain the same ---
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, context={'request': request})
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
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
    parent_models = [('course', Course)]

class TasksListView(BaseListView):
    model = Task
    serializer_class = TaskSerializer
    form_class = TaskForm
    parent_models = [('course', Course), ('unit', Unit)]

    def get_queryset(self, request, *args, **kwargs):
            unit_id = kwargs.get('unit_id')
            course_id = kwargs.get('course_id')
            if unit_id is None or course_id is None:
                raise Http404("URL must contain course_id and unit_id.")

            unit = get_object_or_404(
                Unit,
                id=unit_id,
                course_id=course_id,
                course__student=request.user
            )
            return Task.objects.filter(unit=unit)

    
class TaskDetailView(BaseDetailView):
    model = Task
    serializer_class = TaskSerializer
    parent_models = [('course', Course), ('unit', Unit)]


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

