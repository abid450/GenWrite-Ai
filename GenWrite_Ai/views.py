from django.shortcuts import render
from django.db import transaction
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from Ai_Model.models import ContentGenerationTasks, BatchJob
from Ai_Model.serializers import *
from .permissions import IsOwnerOrAdmin, IsContentTypeAdmin
from rest_framework.permissions import AllowAny
from .filters import ContentTaskFilter, BatchJobFilter
from .paginations import CustomPageNumberPagination, SmallPagination
from GenWrite_Ai.throttles import ConatentGenerationThrottle, BulkGenerationThrottle
from Ai_Model.models import UserProfile

from accounts.tasks import generate_content_task, process_batch_job
# Create your views here.



class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.filter(is_active=True)
    serializer_class = ContentTypeSerializers
    permission_classes = [AllowAny]
    pagination_class = SmallPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['name', 'display_name', 'price_per_token', 'created_at']
    ordering = ['display_name'] 



# ============================================
# 2. ContentTask ViewSet (Main ViewSet)
# ============================================

class ContentTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for content generation tasks
    Provides CRUD + custom actions for generation
    """
    
    serializer_class = ContentGenerationTaskSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContentTaskFilter
    search_fields = ['prompt', 'generated_content', 'request_id']
    ordering_fields = ['created_at', 'processing_time', 'tokens_used', 'cost']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter tasks by current user (admin sees all)"""
        user = self.request.user
        if user.is_staff:
            return ContentGenerationTasks.objects.all()
        return ContentGenerationTasks.objects.filter(user=user)
    
    # ========================================
    # Custom Action: Generate Content
    # ========================================
   # apps/content/views.py - সম্পূর্ণ ফাংশন

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_content(self, request):
        if not request.user.is_authenticated:
            return Response({
            'success': False,
            'message': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Create profile if not exists (backward compatibility)
        if not hasattr(request.user, 'profile'):
            UserProfile.objects.create(user=request.user)
        
        serializer = ContentGenerationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Validation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        data = serializer.validated_data
            # Credit check
        profile = request.user.profile
        if profile.monthly_token_used >= profile.monthly_token_limit:
            return Response({
                'success': False,
                'message': 'Insufficient credits. Please upgrade your plan.',
                'current_credits': profile.monthly_token_used,
                'limit': profile.monthly_token_limit
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
        # Create task
        with transaction.atomic():
            task = ContentGenerationTasks.objects.create(
                user=request.user,
                content_type_id=data['content_type_id'],
                prompt=data['prompt'],
                parameters=data.get('parameters', {}),
                status='pending'
            )
                # Start async task
        celery_task = generate_content_task.delay(str(task.id))
        task.celery_task_id = celery_task.id
        task.save(update_fields=['celery_task_id'])
        return Response({
            'success': True,
            'data': {
                'task_id': str(task.id),
                'request_id': task.request_id,
                'status': 'pending',
                'estimated_time': 30
                }, 'message': 'Content generation started'
                }, status=status.HTTP_202_ACCEPTED)
    
    # ========================================
    # Custom Action: Bulk Generate
    # ========================================
    @action(detail=False, methods=['post'], url_path='bulk-generate',
            throttle_classes=[BulkGenerationThrottle])
    
    def bulk_generate(self, request):
        """
        Bulk generate multiple contents
        POST: /api/content/tasks/bulk-generate/
        """
        serializer = BulkContentGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        requests_data = data['requests']
        
        # Check credits for all requests
        if not request.user.profile.has_remaining_credits():
            return Response({
                'success': False,
                'message': 'Insufficient credits'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        with transaction.atomic():
            tasks = []
            for req in requests_data:
                task = ContentGenerationTasks.objects.create(
                    user=request.user,
                    content_type_id=req['content_type_id'],
                    prompt=req['prompt'],
                    parameters=req.get('parameters', {}),
                    status='pending'
                )
                tasks.append(task)
            
            batch_job = BatchJob.objects.create(
                user=request.user,
                name=data.get('batch_name', ''),
                total_tasks=len(tasks),
                status='pending'
            )
            batch_job.tasks.add(*tasks)
        
        # Start batch processing
        process_batch_job.delay(str(batch_job.id))
        
        return Response({
            'success': True,
            'data': {
                'batch_id': str(batch_job.id),
                'total_tasks': len(tasks),
                'task_ids': [str(t.id) for t in tasks],
                'status': 'pending',
                'estimated_time': len(tasks) * 2
            },
            'message': f'Batch processing started for {len(tasks)} tasks'
        }, status=status.HTTP_202_ACCEPTED)
    
    # ========================================
    # Custom Action: Cancel Task
    # ========================================
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_task(self, request, pk=None):
        """
        Cancel a pending or processing task
        POST: /api/content/tasks/{id}/cancel/
        """
        task = self.get_object()
        
        if task.status not in ['pending', 'processing', 'queued']:
            return Response({
                'success': False,
                'message': f'Task cannot be cancelled. Current status: {task.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Revoke Celery task
        if task.celery_task_id:
            from celery import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)
        
        task.status = 'cancelled'
        task.save(update_fields=['status'])
        
        return Response({
            'success': True,
            'message': 'Task cancelled successfully',
            'data': {'task_id': str(task.id)}
        })
    
    # ========================================
    # Custom Action: Retry Failed Task
    # ========================================
    @action(detail=True, methods=['post'], url_path='retry')
    def retry_task(self, request, pk=None):
        """
        Retry a failed task
        POST: /api/content/tasks/{id}/retry/
        """
        failed_task = self.get_object()
        
        if failed_task.status != 'failed':
            return Response({
                'success': False,
                'message': f'Only failed tasks can be retried. Current status: {failed_task.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if failed_task.retry_count >= failed_task.max_retries:
            return Response({
                'success': False,
                'message': f'Task has reached maximum retry limit ({failed_task.max_retries})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check credits
        if not request.user.profile.has_remaining_credits():
            return Response({
                'success': False,
                'message': 'Insufficient credits'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Create new task with same data
        with transaction.atomic():
            new_task = ContentGenerationTasks.objects.create(
                user=request.user,
                content_type=failed_task.content_type,
                prompt=failed_task.prompt,
                parameters=failed_task.parameters,
                status='pending',
                retry_count=failed_task.retry_count + 1,
                metadata={'original_task_id': str(failed_task.id), **failed_task.metadata}
            )
        
        # Start new generation
        celery_task = generate_content_task.delay(str(new_task.id))
        new_task.celery_task_id = celery_task.id
        new_task.save(update_fields=['celery_task_id'])
        
        return Response({
            'success': True,
            'data': {
                'new_task_id': str(new_task.id),
                'original_task_id': str(failed_task.id),
                'status': 'pending',
                'retry_count': new_task.retry_count
            },
            'message': 'Task regeneration started'
        }, status=status.HTTP_202_ACCEPTED)
    
    # ========================================
    # Custom Action: Get Dashboard Stats
    # ========================================
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard_stats(self, request):
        """
        Get dashboard statistics for current user
        GET: /api/content/tasks/dashboard/
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Basic stats
        stats = queryset.aggregate(
            total_tasks=Count('id'),
            completed_tasks=Count('id', filter=Q(status='completed')),
            pending_tasks=Count('id', filter=Q(status='pending')),
            processing_tasks=Count('id', filter=Q(status='processing')),
            failed_tasks=Count('id', filter=Q(status='failed')),
            cancelled_tasks=Count('id', filter=Q(status='cancelled')),
            avg_processing_time=Avg('processing_time', filter=Q(status='completed')),
            total_tokens_used=Sum('tokens_used'),
            total_cost=Sum('cost')
        )
        
        # Completion rate
        total = stats['total_tasks'] or 1
        completion_rate = round((stats['completed_tasks'] or 0) / total * 100, 2)
        
        # Daily stats (last 7 days)
        last_7_days = timezone.now() - timezone.timedelta(days=7)
        daily_stats = queryset.filter(
            created_at__gte=last_7_days
        ).extra(
            {'day': "DATE(created_at)"}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_tasks': stats['total_tasks'] or 0,
                    'completed_tasks': stats['completed_tasks'] or 0,
                    'pending_tasks': stats['pending_tasks'] or 0,
                    'processing_tasks': stats['processing_tasks'] or 0,
                    'failed_tasks': stats['failed_tasks'] or 0,
                    'cancelled_tasks': stats['cancelled_tasks'] or 0,
                    'completion_rate': completion_rate,
                    'avg_processing_time': round(stats['avg_processing_time'] or 0, 2),
                    'total_tokens_used': stats['total_tokens_used'] or 0,
                    'total_cost': round(stats['total_cost'] or 0, 4)
                },
                'daily_stats': list(daily_stats)
            },
            'message': 'Dashboard statistics retrieved'
        })
    
    # ========================================
    # Custom Action: Get Status Summary
    # ========================================
    @action(detail=False, methods=['get'], url_path='status-summary')
    def status_summary(self, request):
        """
        Get status summary counts
        GET: /api/content/tasks/status-summary/
        """
        queryset = self.get_queryset()
        
        status_counts = queryset.values('status').annotate(count=Count('id'))
        
        return Response({
            'success': True,
            'data': {item['status']: item['count'] for item in status_counts},
            'message': 'Status summary retrieved'
        })


# ============================================
# 3. BatchJob ViewSet
# ============================================

class BatchJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for batch jobs (Read-only)
    - List: GET /api/content/batches/
    - Retrieve: GET /api/content/batches/{id}/
    """
    
    serializer_class = BatchJobSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BatchJobFilter
    ordering_fields = ['created_at', 'completed_at', 'total_tasks']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BatchJob.objects.all()
        return BatchJob.objects.filter(user=user)
    
    # ========================================
    # Custom Action: Get Batch Progress
    # ========================================
    @action(detail=True, methods=['get'], url_path='progress')
    def batch_progress(self, request, pk=None):
        """
        Get detailed progress of a batch job
        GET: /api/content/batches/{id}/progress/
        """
        batch = self.get_object()
        batch.update_progress()
        
        # Get task status distribution
        task_stats = batch.tasks.values('status').annotate(count=Count('id'))
        
        return Response({
            'success': True,
            'data': {
                'batch_id': str(batch.id),
                'name': batch.name,
                'status': batch.status,
                'total_tasks': batch.total_tasks,
                'completed_tasks': batch.completed_tasks,
                'failed_tasks': batch.failed_tasks,
                'progress_percentage': batch.get_progress_percentage(),
                'task_status_distribution': {item['status']: item['count'] for item in task_stats},
                'created_at': batch.created_at,
                'completed_at': batch.completed_at
            },
            'message': 'Batch progress retrieved'
        })
