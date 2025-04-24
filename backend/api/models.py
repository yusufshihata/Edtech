from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import PROTECT
from django.utils import timezone

# Create your models here.
class Learner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    birth_date = models.DateField()

    def __str__(self):
        return self.user.username

class Skill(models.Model):
    name = models.CharField(max_length=200)
    learner = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

class Reason(models.Model):
    learning_reason = models.CharField(max_length=100)

    def __str__(self):
        return self.learning_reason

class SkillReason(models.Model):
    reason = models.OneToOneField(Reason, on_delete=models.CASCADE)
    skill = models.OneToOneField(Skill, on_delete=models.CASCADE)

class Unit(models.Model):
    title = models.CharField(max_length=100)
    skill_reason_pair = models.ForeignKey(SkillReason, on_delete=models.CASCADE, related_name='units')
    deadline = models.DateField()

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title


