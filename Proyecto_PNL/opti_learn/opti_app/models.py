import uuid
from django.conf import settings
from django.db import models


class Problem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='problems'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    objective_expr = models.TextField()
    variables = models.JSONField(default=list)
    constraints_raw = models.JSONField(default=list, blank=True)
    is_quadratic = models.BooleanField(default=False)
    has_equalities = models.BooleanField(default=False)
    has_inequalities = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.id})"


class Constraint(models.Model):
    KIND_CHOICES = (
        ('eq', 'Equality'),
        ('le', 'LessOrEqual'),
        ('ge', 'GreaterOrEqual'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='constraints')
    kind = models.CharField(max_length=2, choices=KIND_CHOICES)
    expr = models.TextField()
    normalized = models.TextField(blank=True)

    def __str__(self):
        return f"{self.kind}: {self.expr}"


class Solution(models.Model):
    STATUS_CHOICES = (
        ('ok', 'OK'),
        ('infeasible', 'Infeasible'),
        ('timeout', 'Timeout'),
        ('error', 'Error'),
        ('not_implemented', 'Not Implemented'),
    )
    METHOD_CHOICES = (
        ('differential', 'Differential'),
        ('lagrange', 'Lagrange'),
        ('kkt', 'KKT'),
        ('gradient', 'Gradient'),
        ('qp', 'Quadratic Programming'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solutions')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    x_star = models.JSONField(default=list)
    f_star = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ok')
    iterations_count = models.IntegerField(default=0)
    tolerance = models.FloatField(default=1e-6)
    runtime_ms = models.IntegerField(null=True, blank=True)
    explanation_final = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Iteration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='iterations')
    k = models.IntegerField()
    x_k = models.JSONField(default=list)
    f_k = models.FloatField(null=True, blank=True)
    grad_norm = models.FloatField(null=True, blank=True)
    step = models.FloatField(null=True, blank=True)
    line_search = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (('solution', 'k'),)


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
