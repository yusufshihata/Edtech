from django.contrib import admin
from .models import Learner, Skill, Unit, Task

# Register your models here.
admin.site.register(Learner)
admin.site.register(Skill)
admin.site.register(Unit)
admin.site.register(Task)
