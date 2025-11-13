from django.contrib import admin
from .models import Problem, Constraint, Solution, Iteration, ChatSession, ChatMessage


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "created_at", "is_quadratic")
    search_fields = ("title", "objective_expr")
    list_filter = ("is_quadratic", "has_equalities", "has_inequalities")


@admin.register(Constraint)
class ConstraintAdmin(admin.ModelAdmin):
    list_display = ("id", "problem", "kind")
    list_filter = ("kind",)


class IterationInline(admin.TabularInline):
    model = Iteration
    extra = 0


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("id", "problem", "method", "status", "iterations_count", "created_at")
    list_filter = ("method", "status")
    inlines = [IterationInline]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "active", "created_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    list_filter = ("role",)

