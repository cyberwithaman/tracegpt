from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
import time
import json
from django.conf import settings
from django.urls import reverse
from django.db.models import Count, Avg, Sum, Min, Max, F
from django.db.models.functions import TruncDay, TruncHour

import uuid
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import timedelta

from .models import ChatExample, ChatTrace, TraceStep, ContactMessage
from .langsmith_utils import TracerManager
from .analytics import ChartDataGenerator
from .visualizations import DashboardVisualizations

def home(request):
    """Home page with chat interface"""
    examples = ChatExample.objects.all().order_by('-created_at')
    selected_example_id = request.GET.get('example_id')
    selected_example = None
    
    if selected_example_id:
        selected_example = get_object_or_404(ChatExample, id=selected_example_id)
    
    context = {
        'examples': examples,
        'selected_example': selected_example
    }
    
    return render(request, 'home.html', context)

def process_chat(request):
    """Process a chat input and return a traced response"""
    if request.method == 'POST':
        input_prompt = request.POST.get('input_prompt')
        example_id = request.POST.get('example_id')
        
        # Track overall execution time
        start_time = time.time()
        
        # Initialize LangSmith tracer
        tracer = TracerManager()
        
        # Get example if provided
        example = None
        if example_id:
            try:
                example = ChatExample.objects.get(id=example_id)
            except ChatExample.DoesNotExist:
                pass
        
        # Start trace
        metadata = {"source": "web_interface", "user_id": request.user.id if request.user.is_authenticated else "anonymous"}
        run_tree = tracer.start_trace(input_prompt, metadata)
        
        # Process input
        processed_input = tracer.process_input(run_tree, input_prompt)
        
        # Generate response
        response = tracer.generate_response(run_tree, processed_input)
        
        # Postprocess response
        final_response = tracer.postprocess_response(run_tree, response)
        
        # Evaluate response if we have an example
        if example:
            evaluation = tracer.evaluate_response(run_tree, response, example.expected_response)
        else:
            evaluation = tracer.evaluate_response(run_tree, response)
        
        # End trace
        trace_data = tracer.end_trace(run_tree, final_response)
        
        # Calculate total execution time
        end_time = time.time()
        runtime_seconds = end_time - start_time
        
        # Save trace to database
        chat_trace = ChatTrace.objects.create(
            run_id=run_tree.id,
            input_prompt=input_prompt,
            output_response=response,
            status='success',
            runtime_seconds=runtime_seconds,
            trace_data=trace_data,
        )
        
        # Add tags if using an example
        if example:
            chat_trace.tags = example.tags
            chat_trace.save()
        
        # Create step records
        for child_run in tracer.get_children(run_tree.id):
            TraceStep.objects.create(
                trace=chat_trace,
                step_name=child_run.name,
                step_type=child_run.run_type,
                input_data=child_run.inputs,
                output_data=child_run.outputs,
                start_time=child_run.start_time,
                end_time=child_run.end_time,
                runtime_seconds=(child_run.end_time - child_run.start_time).total_seconds()
            )
            
        # Prepare response data
        response_data = {
            'success': True,
            'response': response,
            'trace_id': chat_trace.id,
            'runtime': runtime_seconds,
            'steps': [
                {
                    'name': step.step_name,
                    'type': step.step_type,
                    'runtime': step.runtime_seconds
                } for step in chat_trace.steps.all()
            ]
        }
        
        return JsonResponse(response_data)
        
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def logs(request):
    """Display logs of traced chats"""
    filter_tag = request.GET.get('tag')
    search_query = request.GET.get('query')
    
    traces = ChatTrace.objects.all()
    
    # Filter by tag if provided
    if filter_tag:
        traces = traces.filter(tags__contains=filter_tag)
    
    # Search if query provided
    if search_query:
        traces = traces.filter(input_prompt__icontains=search_query) | traces.filter(output_response__icontains=search_query)
    
    # Paginate
    paginator = Paginator(traces, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_tag': filter_tag,
        'search_query': search_query,
        'available_tags': set([tag for trace in ChatTrace.objects.all() for tag in trace.tags])
    }
    
    return render(request, 'logs.html', context)

def trace_detail(request, trace_id):
    """Display detail of a specific trace"""
    trace = get_object_or_404(ChatTrace, id=trace_id)
    steps = trace.steps.all()
    
    context = {
        'trace': trace,
        'steps': steps,
        'trace_data_json': json.dumps(trace.trace_data, indent=2)
    }
    
    return render(request, 'trace_detail.html', context)

def export_trace(request, trace_id):
    """Export trace data as JSON"""
    trace = get_object_or_404(ChatTrace, id=trace_id)
    
    response = JsonResponse(trace.trace_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="trace_{trace.id}.json"'
    
    return response
    
def contact(request):
    """Contact page with form handling"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message_content = request.POST.get('message')
        
        # Check if all required fields are provided
        if name and email and phone and message_content:
            # Save the contact message to the database
            contact_message = ContactMessage(
                name=name,
                email=email,
                phone=phone,
                message=message_content
            )
            contact_message.save()
            
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, "Please fill out all required fields.")
    
    # Get recent contact messages for admin demo purposes (normally not shown to regular users)
    recent_messages = None
    if request.user.is_staff:
        recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]
    
    return render(request, 'contact.html', {'recent_messages': recent_messages})

def analytics_dashboard(request):
    """View for displaying the analytics dashboard"""
    # Get high-level metrics
    trace_count = ChatTrace.objects.count()
    example_count = ChatExample.objects.count()
    contact_count = ContactMessage.objects.count()
    
    if trace_count > 0:
        avg_runtime = ChatTrace.objects.aggregate(avg=Avg('runtime_seconds'))['avg']
        max_runtime = ChatTrace.objects.aggregate(max=Max('runtime_seconds'))['max']
    else:
        avg_runtime = 0
        max_runtime = 0
    
    # Get recent traces
    recent_traces = ChatTrace.objects.order_by('-created_at')[:5]
    
    # Generate tags histogram
    tags_data = ChartDataGenerator.tags_distribution()
    
    # Get traces by status
    status_data = ChatTrace.objects.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in status_data}
    
    context = {
        'trace_count': trace_count,
        'example_count': example_count,
        'contact_count': contact_count,
        'avg_runtime': round(avg_runtime, 2) if avg_runtime else 0,
        'max_runtime': round(max_runtime, 2) if max_runtime else 0,
        'recent_traces': recent_traces,
        'tags_data': tags_data,
        'status_counts': status_counts,
    }
    
    return render(request, 'analytics.html', context)

def api_traces_summary(request):
    """API endpoint for traces summary data"""
    days = int(request.GET.get('days', 30))
    chart_data = ChartDataGenerator.traces_by_date(days)
    return JsonResponse(chart_data)

def api_trace_stats(request):
    """API endpoint for trace statistics"""
    metrics = ChartDataGenerator.trace_performance_metrics()
    return JsonResponse(metrics)

def model_visualizations(request):
    """View for displaying comprehensive model visualizations dashboard"""
    # Get all visualizations
    visualizations = DashboardVisualizations.get_all_visualizations()
    
    # Get existing chart images for compatibility with old templates
    runtime_distribution_img = ChartDataGenerator.generate_matplotlib_chart('runtime_histogram')
    traces_by_date_img = ChartDataGenerator.generate_matplotlib_chart('trace_count_by_day')
    tags_distribution_img = ChartDataGenerator.generate_matplotlib_chart('tags_pie')
    step_runtime_img = ChartDataGenerator.generate_matplotlib_chart('step_runtime')
    
    context = {
        'title': 'Model Data Visualizations',
        'visualizations': visualizations,
        'runtime_distribution_img': runtime_distribution_img,
        'traces_by_date_img': traces_by_date_img,
        'tags_distribution_img': tags_distribution_img,
        'step_runtime_img': step_runtime_img,
    }
    
    return render(request, 'visualizations.html', context)
