from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('process_chat/', views.process_chat, name='process_chat'),
    path('logs/', views.logs, name='logs'),
    path('trace/<int:trace_id>/', views.trace_detail, name='trace_detail'),
    path('trace/<int:trace_id>/export/', views.export_trace, name='export_trace'),
    path('contact/', views.contact, name='contact'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('visualizations/', views.model_visualizations, name='model_visualizations'),
    path('api/analytics/traces_summary/', views.api_traces_summary, name='api_traces_summary'),
    path('api/analytics/trace_stats/', views.api_trace_stats, name='api_trace_stats'),
] 