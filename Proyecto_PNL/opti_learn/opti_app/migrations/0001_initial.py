from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('objective_expr', models.TextField()),
                ('variables', models.JSONField(default=list)),
                ('constraints_raw', models.JSONField(default=list, blank=True)),
                ('is_quadratic', models.BooleanField(default=False)),
                ('has_equalities', models.BooleanField(default=False)),
                ('has_inequalities', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(related_name='problems', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('method', models.CharField(max_length=20, choices=[('differential', 'Differential'), ('lagrange', 'Lagrange'), ('kkt', 'KKT'), ('gradient', 'Gradient'), ('qp', 'Quadratic Programming')])),
                ('x_star', models.JSONField(default=list)),
                ('f_star', models.FloatField(null=True, blank=True)),
                ('status', models.CharField(max_length=20, default='ok', choices=[('ok', 'OK'), ('infeasible', 'Infeasible'), ('timeout', 'Timeout'), ('error', 'Error'), ('not_implemented', 'Not Implemented')])),
                ('iterations_count', models.IntegerField(default=0)),
                ('tolerance', models.FloatField(default=1e-06)),
                ('runtime_ms', models.IntegerField(null=True, blank=True)),
                ('explanation_final', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('problem', models.ForeignKey(related_name='solutions', on_delete=django.db.models.deletion.CASCADE, to='opti_app.problem')),
            ],
        ),
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('kind', models.CharField(max_length=2, choices=[('eq', 'Equality'), ('le', 'LessOrEqual'), ('ge', 'GreaterOrEqual')])),
                ('expr', models.TextField()),
                ('normalized', models.TextField(blank=True)),
                ('problem', models.ForeignKey(related_name='constraints', on_delete=django.db.models.deletion.CASCADE, to='opti_app.problem')),
            ],
        ),
        migrations.CreateModel(
            name='Iteration',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('k', models.IntegerField()),
                ('x_k', models.JSONField(default=list)),
                ('f_k', models.FloatField(null=True, blank=True)),
                ('grad_norm', models.FloatField(null=True, blank=True)),
                ('step', models.FloatField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('solution', models.ForeignKey(related_name='iterations', on_delete=django.db.models.deletion.CASCADE, to='opti_app.solution')),
            ],
            options={
                'unique_together': {('solution', 'k')},
            },
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('problem', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='opti_app.problem')),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('role', models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')])),
                ('content', models.TextField()),
                ('payload', models.JSONField(default=dict, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(related_name='messages', on_delete=django.db.models.deletion.CASCADE, to='opti_app.chatsession')),
            ],
        ),
    ]

