from rest_framework import serializers
from .models import ContentType, ContentGenerationTasks, BatchJob


class ContentTypeSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = ContentType
        fields = ['id', 'name', 'display_name', 'system_prompt', 'default_tokens',
                  'price_per_token', 'is_active', 'created_at']
        
        read_only_fields = ['id', 'created_at']



class ContentGenerationTaskSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    content_type_name = serializers.CharField(source='content_type.display_name', read_only=True)

    class Meta:
        model = ContentGenerationTasks
        fields = [
            'id', 'request_id', 'user', 'user_email', 'content_type', 'content_type_name',
            'prompt', 'generated_content', 'status', 'celery_task_id', 'parameters',
            'processing_time', 'tokens_used', 'cost', 'retry_count', 'max_retries',
            'metadata', 'error_message', 'created_at', 'updated_at', 'started_at', 'completed_at'
        ]


        extra_kwargs = {
            'id': {'read_only': True},
            'request_id': {'read_only': True},
            'user': {'read_only': True},
            'celery_task_id': {'read_only': True},
            'generated_content': {'read_only': True},
            'processing_time': {'read_only': True},
            'tokens_used': {'read_only': True},
            'cost': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            
            # prompt এবং parameters শুধু write_only (POST এ লাগবে)
            'prompt': {'write_only': True},
            'parameters': {'write_only': True},
        }
    

    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    


class ContentGenerationCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=5000, help_text='User prompt for content generation')
    content_type_id = serializers.IntegerField(help_text='Type of content to generate')
    parameters = serializers.DictField(required=False, default=dict)

    def validate_content_type_id(self, value):
        try:
            ContentType.objects.get(id=value, is_active=True)
            return value
        
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f'Content type with id {value} does not exist or is inactive')
        


class BulkContentGenerationSerializer(serializers.Serializer):
    """Serializer for bulk content generation"""
    
    requests = serializers.ListField(
        child=ContentGenerationCreateSerializer(),
        min_length=1,
        max_length=100,
        help_text="List of content generation requests"
    )
    batch_name = serializers.CharField(required=False, max_length=200)


class BatchJobSerializer(serializers.ModelSerializer):
    """Serializer for BatchJob"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchJob
        fields = [
            'id', 'user', 'user_email', 'name', 'total_tasks', 'completed_tasks',
            'failed_tasks', 'status', 'celery_group_id', 'created_at', 'completed_at',
            'progress_percentage'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'completed_at']
    
    def get_progress_percentage(self, obj):
        if obj.total_tasks > 0:
            return round((obj.completed_tasks / obj.total_tasks * 100), 2)
        return 0


class TaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status"""
    
    status = serializers.ChoiceField(choices=ContentGenerationTasks.STATUS_CHOICES)
    error_message = serializers.CharField(required=False, allow_blank=True)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    processing_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    cancelled_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_processing_time = serializers.FloatField()
    total_tokens_used = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=6)
    daily_stats = serializers.ListField()
        
