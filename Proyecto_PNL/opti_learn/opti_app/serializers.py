from rest_framework import serializers
from .models import Problem, Constraint, Solution, Iteration, ChatSession, ChatMessage


class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = ['id', 'kind', 'expr', 'normalized']


class ProblemSerializer(serializers.ModelSerializer):
    constraints = ConstraintSerializer(source='constraints', many=True, read_only=True)

    class Meta:
        model = Problem
        fields = [
            'id', 'owner', 'title', 'description', 'objective_expr', 'variables',
            'constraints_raw', 'is_quadratic', 'has_equalities', 'has_inequalities',
            'created_at', 'updated_at', 'constraints'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class IterationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Iteration
        fields = ['id', 'k', 'x_k', 'f_k', 'grad_norm', 'step', 'line_search', 'notes']


class SolutionSerializer(serializers.ModelSerializer):
    iterations = IterationSerializer(many=True, read_only=True)

    class Meta:
        model = Solution
        fields = [
            'id', 'problem', 'method', 'x_star', 'f_star', 'status',
            'iterations_count', 'tolerance', 'runtime_ms', 'explanation_final',
            'created_at', 'iterations'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'problem', 'created_at', 'active']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'role', 'content', 'payload', 'created_at']


class ParseRequestSerializer(serializers.Serializer):
    objective_expr = serializers.CharField()
    variables = serializers.ListField(child=serializers.CharField(), required=False)
    constraints = serializers.ListField(child=serializers.DictField(), required=False)
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
