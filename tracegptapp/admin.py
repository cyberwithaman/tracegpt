from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils.translation import gettext_lazy as _

from .models import ChatExample, ChatTrace, TraceStep, ContactMessage
from .analytics import ChartDataGenerator
from .visualizations import DashboardVisualizations

# Custom admin theme
admin.site.site_header = "TraceGPT Admin Dashboard"
admin.site.site_title = "TraceGPT Analytics Portal"
admin.site.index_title = "Welcome to TraceGPT Analytics"

class TraceStepInline(admin.TabularInline):
    model = TraceStep
    extra = 0
    readonly_fields = ('step_name', 'step_type', 'runtime_display', 'start_time', 'end_time')
    can_delete = False
    fields = ('step_name', 'step_type', 'runtime_display', 'start_time', 'end_time')
    
    def has_add_permission(self, request, obj=None):
        return False
        
    def runtime_display(self, obj):
        """Display runtime with color coding"""
        if obj.runtime_seconds < 1:
            color = "green"
        elif obj.runtime_seconds < 3:
            color = "orange"
        else:
            color = "red"
        # Format the number before passing it to format_html
        formatted_runtime = f"{obj.runtime_seconds:.2f}s"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, formatted_runtime)
    
    runtime_display.short_description = "Runtime"

@admin.register(ChatExample)
class ChatExampleAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_tags', 'created_at')
    list_filter = ('tags', 'created_at')
    search_fields = ('title', 'input_prompt', 'expected_response')
    fieldsets = (
        ('Example Information', {
            'fields': ('title', 'tags')
        }),
        ('Chat Content', {
            'fields': ('input_prompt', 'expected_response'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    
    def get_tags(self, obj):
        """Display tags with color coding"""
        tags_html = []
        
        for tag in obj.tags:
            if tag == 'correct':
                color = '#28a745'  # green
            elif tag == 'misleading':
                color = '#ffc107'  # yellow
            elif tag == 'incomplete':
                color = '#17a2b8'  # blue
            elif tag == 'slow':
                color = '#dc3545'  # red
            else:
                color = '#6c757d'  # gray
                
            tags_html.append(
                f'<span style="background-color: {color}; color: white; padding: 3px 8px; '
                f'border-radius: 12px; font-size: 0.8em;">{tag}</span>'
            )
            
        return format_html(' '.join(tags_html))
    
    get_tags.short_description = 'Tags'

@admin.register(ChatTrace)
class ChatTraceAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'status_badge', 'get_tags', 'runtime_display', 'created_at')
    list_filter = ('status', 'tags', 'created_at')
    search_fields = ('run_id', 'input_prompt', 'output_response')
    inlines = [TraceStepInline]
    readonly_fields = ('run_id', 'input_prompt', 'output_response', 'status',
                      'tags', 'runtime_seconds', 'trace_data', 'created_at')
    
    fieldsets = (
        ('Trace Information', {
            'fields': ('run_id', 'status', 'tags', 'runtime_seconds')
        }),
        ('Chat Content', {
            'fields': ('input_prompt', 'output_response'),
            'classes': ('wide',)
        }),
        ('Trace Data', {
            'fields': ('trace_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    change_list_template = 'admin/tracegptapp/chattrace_change_list.html'
    
    def get_tags(self, obj):
        """Display tags with color coding"""
        if not obj.tags:
            return '-'
            
        tags_html = []
        
        for tag in obj.tags:
            if tag == 'correct':
                color = '#28a745'  # green
            elif tag == 'misleading':
                color = '#ffc107'  # yellow
            elif tag == 'incomplete':
                color = '#17a2b8'  # blue
            elif tag == 'slow':
                color = '#dc3545'  # red
            else:
                color = '#6c757d'  # gray
                
            tags_html.append(
                f'<span style="background-color: {color}; color: white; padding: 3px 8px; '
                f'border-radius: 12px; font-size: 0.8em;">{tag}</span>'
            )
            
        return format_html(' '.join(tags_html))
    
    get_tags.short_description = 'Tags'
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        if obj.status == 'success':
            color = '#28a745'  # green
        else:
            color = '#dc3545'  # red
            
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px;">{}</span>',
            color, obj.status
        )
    
    status_badge.short_description = 'Status'
    
    def runtime_display(self, obj):
        """Display runtime with color coding"""
        if obj.runtime_seconds < 1:
            color = "green"
        elif obj.runtime_seconds < 3:
            color = "orange"
        else:
            color = "red"
        # Format the number before passing it to format_html
        formatted_runtime = f"{obj.runtime_seconds:.2f}s"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, formatted_runtime)
    
    runtime_display.short_description = "Runtime"
    
    def has_add_permission(self, request):
        return False
        
    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path('charts/traces_by_date/', self.admin_site.admin_view(self.traces_by_date_view), 
                name='chattrace_traces_by_date'),
            path('charts/runtime_distribution/', self.admin_site.admin_view(self.runtime_distribution_view), 
                name='chattrace_runtime_distribution'),
            path('charts/tags_distribution/', self.admin_site.admin_view(self.tags_distribution_view), 
                name='chattrace_tags_distribution'),
            path('charts/step_runtime/', self.admin_site.admin_view(self.step_runtime_view), 
                name='chattrace_step_runtime'),
            path('charts/matplotlib/<str:chart_type>/', self.admin_site.admin_view(self.matplotlib_chart_view), 
                name='chattrace_matplotlib_chart'),
            path('reports/performance/', self.admin_site.admin_view(self.performance_report_view),
                name='chattrace_performance_report'),
            path('visualizations/', self.admin_site.admin_view(self.visualizations_dashboard_view),
                name='visualizations_dashboard'),
        ]
        return extra_urls + urls
    
    def traces_by_date_view(self, request):
        """JSON view for traces by date chart"""
        days = int(request.GET.get('days', 30))
        chart_data = ChartDataGenerator.traces_by_date(days)
        return JsonResponse(chart_data)
    
    def runtime_distribution_view(self, request):
        """JSON view for runtime distribution chart"""
        chart_data = ChartDataGenerator.runtime_distribution()
        return JsonResponse(chart_data)
    
    def tags_distribution_view(self, request):
        """JSON view for tags distribution chart"""
        chart_data = ChartDataGenerator.tags_distribution()
        return JsonResponse(chart_data)
    
    def step_runtime_view(self, request):
        """JSON view for step runtime chart"""
        chart_data = ChartDataGenerator.step_runtime_by_type()
        return JsonResponse(chart_data)
    
    def matplotlib_chart_view(self, request, chart_type):
        """View for matplotlib generated charts"""
        try:
            image_base64 = ChartDataGenerator.generate_matplotlib_chart(chart_type)
            return JsonResponse({'image': image_base64})
        except Exception as e:
            # Log the error and return an error image
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating chart {chart_type}: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
        
    def performance_report_view(self, request):
        """View for performance reports"""
        # Get performance metrics
        metrics = ChartDataGenerator.trace_performance_metrics()
        
        # Get hourly activity data
        hourly_activity = ChartDataGenerator.hourly_activity_heatmap()
        
        context = {
            'title': 'Trace Performance Report',
            'metrics': metrics,
            'hourly_activity': hourly_activity,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tracegptapp/performance_report.html', context)

    def visualizations_dashboard_view(self, request):
        """View for visualizations dashboard"""
        # Get all visualizations
        visualizations = DashboardVisualizations.get_all_visualizations()
        
        # Get existing chart images for compatibility with old templates
        runtime_distribution_img = ChartDataGenerator.generate_matplotlib_chart('runtime_histogram')
        traces_by_date_img = ChartDataGenerator.generate_matplotlib_chart('trace_count_by_day')
        tags_distribution_img = ChartDataGenerator.generate_matplotlib_chart('tags_pie')
        step_runtime_img = ChartDataGenerator.generate_matplotlib_chart('step_runtime')
        
        context = {
            'title': 'Data Visualizations Dashboard',
            'visualizations': visualizations,
            'runtime_distribution_img': runtime_distribution_img,
            'traces_by_date_img': traces_by_date_img,
            'tags_distribution_img': tags_distribution_img,
            'step_runtime_img': step_runtime_img,
            'opts': self.model._meta,
        }
        return render(request, 'admin/tracegptapp/dashboard_visualizations.html', context)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message Details', {
            'fields': ('message', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        if obj.status == 'new':
            color = '#007bff'  # blue
        elif obj.status == 'in_progress':
            color = '#ffc107'  # yellow
        elif obj.status == 'completed':
            color = '#28a745'  # green
        else:
            color = '#dc3545'  # red
            
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px;">{}</span>',
            color, obj.status
        )
    
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if change and form.cleaned_data.get('status') != form.initial.get('status'):
            # You could add logging or notification when status changes
            pass
        super().save_model(request, obj, form, change)
