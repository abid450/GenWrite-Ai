import django_filters
from django_filters import rest_framework as filters
from Ai_Model.models import ContentGenerationTasks, BatchJob


class ContentTaskFilter(filters.FilterSet):
    """Filter for ContentGenerationTask"""
    
    status = filters.ChoiceFilter(choices=ContentGenerationTasks.STATUS_CHOICES)
    content_type = filters.NumberFilter(field_name='content_type__id')
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    min_tokens = filters.NumberFilter(field_name='tokens_used', lookup_expr='gte')
    max_tokens = filters.NumberFilter(field_name='tokens_used', lookup_expr='lte')
    search = filters.CharFilter(field_name='prompt', lookup_expr='icontains')
    
    class Meta:
        model = ContentGenerationTasks
        fields = ['status', 'content_type', 'created_at_after', 'created_at_before', 
                  'min_tokens', 'max_tokens', 'search']


class BatchJobFilter(filters.FilterSet):
    """Filter for BatchJob"""
    
    status = filters.ChoiceFilter(choices=BatchJob.STATUS_CHOICES)
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = BatchJob
        fields = ['status', 'created_at_after', 'created_at_before']