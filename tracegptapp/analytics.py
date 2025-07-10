import matplotlib
# Use Agg backend to avoid GUI threading issues
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from io import BytesIO
import base64
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, fields, Max, Min
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractHour

from .models import ChatTrace, TraceStep, ContactMessage

# Set matplotlib style
plt.style.use('ggplot')
sns.set_palette("viridis")

# Custom color maps
TRACE_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
RUNTIME_CMAP = LinearSegmentedColormap.from_list("runtime_cmap", ["#d0f0c0", "#006400"])
TAG_COLORS = {'correct': '#28a745', 'misleading': '#ffc107', 'incomplete': '#17a2b8', 'slow': '#dc3545'}

class ChartDataGenerator:
    @staticmethod
    def traces_by_date(days=30):
        """Generate data for traces created over time chart with pandas"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get the data from database
        traces = ChatTrace.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            date=TruncDay('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Convert to pandas dataframe for analysis
        df = pd.DataFrame(list(traces))
        
        if df.empty:
            # Create sample data if no data exists
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            df = pd.DataFrame({'date': date_range, 'count': [0] * len(date_range)})
        else:
            # Ensure we have all dates in range (pandas resampling)
            df.set_index('date', inplace=True)
            idx = pd.date_range(start=start_date.date(), end=end_date.date())
            df = df.reindex(idx, fill_value=0).reset_index()
            df.rename(columns={'index': 'date'}, inplace=True)
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in df['date']],
            'counts': df['count'].tolist(),
        }
    
    @staticmethod
    def runtime_distribution():
        """Generate runtime distribution chart data using pandas"""
        traces = ChatTrace.objects.all().values('runtime_seconds')
        
        if not traces:
            return {
                'labels': ['0-1s', '1-2s', '2-3s', '3-5s', '5-10s', '10s+'],
                'data': [0, 0, 0, 0, 0, 0],
            }
        
        # Convert to pandas DataFrame for better analysis
        df = pd.DataFrame(list(traces))
        
        # Create bins for the histogram
        max_runtime = df['runtime_seconds'].max() if len(df) > 0 else 10
        
        # Ensure bins increase monotonically
        if max_runtime <= 10:
            bins = [0, 1, 2, 3, 5, 10, 11]  # Default bins with fixed upper limit
        else:
            bins = [0, 1, 2, 3, 5, 10, max_runtime + 1]  # Adjust top bin for large values
            
        labels = ['0-1s', '1-2s', '2-3s', '3-5s', '5-10s', '10s+']
        
        # Use pandas cut to bin the data
        df['runtime_bin'] = pd.cut(df['runtime_seconds'], bins=bins, labels=labels, right=False)
        
        # Get the counts for each bin
        runtime_counts = df['runtime_bin'].value_counts().reindex(labels).fillna(0)
        
        return {
            'labels': labels,
            'data': runtime_counts.tolist(),
        }
    
    @staticmethod
    def tags_distribution():
        """Generate tags distribution chart data with pandas"""
        # Get all traces
        traces = ChatTrace.objects.all()
        
        if not traces:
            return {
                'labels': ['No Tags'],
                'data': [0],
            }
        
        # Create a list of all tags with their counts
        all_tags = []
        for trace in traces:
            all_tags.extend(trace.tags)
        
        if not all_tags:
            return {
                'labels': ['No Tags'],
                'data': [0],
            }
        
        # Convert to pandas Series for counting
        tags_series = pd.Series(all_tags)
        tag_counts = tags_series.value_counts()
        
        return {
            'labels': tag_counts.index.tolist(),
            'data': tag_counts.values.tolist(),
            'colors': [TAG_COLORS.get(tag, '#6c757d') for tag in tag_counts.index.tolist()]
        }
    
    @staticmethod
    def step_runtime_by_type():
        """Generate average runtime by step type chart data with pandas"""
        steps = TraceStep.objects.values('step_type').annotate(
            avg_runtime=Avg('runtime_seconds')
        ).order_by('-avg_runtime')
        
        if not steps:
            return {
                'labels': ['No Steps'],
                'data': [0],
            }
        
        # Convert to pandas for analysis and sorting
        df = pd.DataFrame(list(steps))
        df.sort_values('avg_runtime', ascending=False, inplace=True)
        
        return {
            'labels': df['step_type'].tolist(),
            'data': [round(x, 2) for x in df['avg_runtime'].tolist()],
        }
    
    @staticmethod
    def hourly_activity_heatmap():
        """Generate hourly activity heatmap data with pandas"""
        # Get all traces with created_at time
        traces = ChatTrace.objects.all().annotate(
            hour=ExtractHour('created_at'),
            day=TruncDay('created_at')
        ).values('hour', 'day').annotate(count=Count('id'))
        
        if not traces:
            # Return empty data
            return {'data': []}
            
        # Convert to pandas DataFrame
        df = pd.DataFrame(list(traces))
        
        # Create pivot table with days as rows and hours as columns
        pivot_data = df.pivot_table(
            index='day', 
            columns='hour', 
            values='count', 
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Format the data for the heatmap
        days = [day.strftime('%Y-%m-%d') for day in pivot_data['day']]
        
        # Create dataset
        dataset = []
        for hour in range(24):
            if hour in pivot_data.columns:
                hour_data = []
                for i, day in enumerate(days):
                    hour_data.append({
                        'x': day,
                        'y': int(pivot_data.iloc[i][hour])
                    })
                dataset.append({
                    'name': f'{hour:02d}:00',
                    'data': hour_data
                })
        
        return {'data': dataset, 'days': days}
    
    @staticmethod
    def contact_status_distribution():
        """Generate contact message status distribution chart data with pandas"""
        statuses = ContactMessage.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        if not statuses:
            return {
                'labels': ['No Messages'],
                'data': [0],
            }
        
        df = pd.DataFrame(list(statuses))
        
        return {
            'labels': df['status'].tolist(),
            'data': df['count'].tolist(),
        }
    
    @staticmethod
    def trace_performance_metrics():
        """Generate performance metrics for traces using pandas"""
        traces = ChatTrace.objects.all().values('runtime_seconds', 'created_at')
        
        if not traces:
            return {
                'avg_runtime': 0,
                'max_runtime': 0,
                'min_runtime': 0,
                'total_traces': 0,
                'trend_data': []
            }
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(list(traces))
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Calculate basic stats
        metrics = {
            'avg_runtime': round(df['runtime_seconds'].mean(), 2),
            'max_runtime': round(df['runtime_seconds'].max(), 2),
            'min_runtime': round(df['runtime_seconds'].min(), 2),
            'total_traces': len(df),
        }
        
        # Calculate trend data (weekly average runtime)
        # Remove timezone info to avoid warnings
        df['created_at'] = df['created_at'].dt.tz_localize(None)
        df['week'] = df['created_at'].dt.to_period('W')
        weekly_avg = df.groupby('week')['runtime_seconds'].mean().reset_index()
        weekly_avg['week'] = weekly_avg['week'].astype(str)
        
        metrics['trend_data'] = {
            'labels': weekly_avg['week'].tolist(),
            'data': [round(x, 2) for x in weekly_avg['runtime_seconds'].tolist()]
        }
        
        return metrics
        
    @staticmethod
    def generate_matplotlib_chart(chart_type):
        """Generate a Matplotlib chart and return as base64 encoded string"""
        try:
            # Set matplotlib style
            plt.style.use('ggplot')
            fig = plt.figure(figsize=(10, 6), dpi=100)
            
            if chart_type == 'runtime_histogram':
                # Get runtime data
                traces = ChatTrace.objects.all().values_list('runtime_seconds', flat=True)
                
                if not traces:
                    plt.text(0.5, 0.5, 'No trace data available', 
                             horizontalalignment='center', verticalalignment='center',
                             fontsize=14)
                else:
                    # Create DataFrame
                    df = pd.DataFrame({'runtime': list(traces)})
                    
                    # Create histogram with seaborn for better styling
                    ax = sns.histplot(df['runtime'], bins=10, kde=True, color='#5470c6')
                    
                    # Add median line
                    median_runtime = df['runtime'].median()
                    plt.axvline(median_runtime, color='#ee6666', linestyle='--', 
                                label=f'Median: {median_runtime:.2f}s')
                    
                    plt.xlabel('Runtime (seconds)')
                    plt.ylabel('Number of Traces')
                    plt.title('Distribution of Trace Runtimes', fontsize=16)
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                
            elif chart_type == 'tags_pie':
                # Get tags data using the pandas function
                tags_data = ChartDataGenerator.tags_distribution()
                
                if tags_data['labels'] == ['No Tags']:
                    plt.text(0.5, 0.5, 'No tag data available', 
                             horizontalalignment='center', verticalalignment='center',
                             fontsize=14)
                else:
                    # Get colors from tags_data if available
                    colors = tags_data.get('colors', sns.color_palette('viridis', len(tags_data['labels'])))
                    
                    # Create the pie chart
                    plt.pie(
                        tags_data['data'], 
                        labels=tags_data['labels'], 
                        autopct='%1.1f%%', 
                        startangle=90, 
                        shadow=True,
                        colors=colors,
                        wedgeprops={'edgecolor': 'white', 'linewidth': 1}
                    )
                    plt.axis('equal')
                    plt.title('Distribution of Tags in Chat Traces', fontsize=16)
                    
            elif chart_type == 'step_runtime':
                # Get step runtime data
                steps = TraceStep.objects.values('step_type').annotate(
                    avg_runtime=Avg('runtime_seconds'),
                    max_runtime=Max('runtime_seconds')
                ).order_by('-avg_runtime')
                
                if not steps:
                    plt.text(0.5, 0.5, 'No step data available', 
                             horizontalalignment='center', verticalalignment='center',
                             fontsize=14)
                else:
                    # Convert to DataFrame
                    df = pd.DataFrame(list(steps))
                    df = df.sort_values('avg_runtime')
                    
                    # Create horizontal bar chart with error bars
                    y_pos = np.arange(len(df['step_type']))
                    
                    # Calculate error as difference between max and average
                    error = df['max_runtime'] - df['avg_runtime']
                    
                    # Plot horizontal bars with gradient colors
                    bars = plt.barh(y_pos, df['avg_runtime'], xerr=error, 
                            alpha=0.8, capsize=5, error_kw={'ecolor': '#ee6666'})
                    
                    # Color bars by runtime (longer runtime = darker color)
                    norm = plt.Normalize(df['avg_runtime'].min(), df['avg_runtime'].max())
                    for i, bar in enumerate(bars):
                        bar.set_color(plt.cm.viridis(norm(df['avg_runtime'].iloc[i])))
                    
                    plt.yticks(y_pos, df['step_type'])
                    plt.xlabel('Average Runtime (seconds)')
                    plt.title('Average Runtime by Step Type (with max runtime error bars)', fontsize=14)
                    plt.grid(True, alpha=0.3, axis='x')
                    plt.tight_layout()
                    
            elif chart_type == 'trace_count_by_day':
                # Get trace count by day for the last 30 days
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
                
                traces = ChatTrace.objects.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).annotate(
                    day=TruncDay('created_at')
                ).values('day').annotate(
                    count=Count('id')
                ).order_by('day')
                
                if not traces:
                    plt.text(0.5, 0.5, 'No trace data available', 
                             horizontalalignment='center', verticalalignment='center',
                             fontsize=14)
                else:
                    # Convert to DataFrame
                    df = pd.DataFrame(list(traces))
                    
                    # Convert timezone-aware dates to naive dates for consistent comparison
                    df['day'] = df['day'].dt.tz_localize(None)
                    
                    # Ensure all dates in range - use naive datetimes
                    date_range = pd.date_range(start=start_date.date(), end=end_date.date())
                    df_all_dates = pd.DataFrame({'day': date_range})
                    
                    # Merge to include all dates
                    df = pd.concat([
                        df_all_dates.set_index('day'),
                        df.set_index('day')
                    ], axis=1).fillna(0).reset_index()
                    
                    # Plot bar chart
                    plt.bar(df['day'], df['count'], color=TRACE_COLORS)
                    plt.xlabel('Date')
                    plt.ylabel('Number of Traces')
                    plt.title('Trace Count by Day (Last 30 Days)', fontsize=16)
                    plt.xticks(rotation=45)
                    plt.grid(True, alpha=0.3, axis='y')
                    plt.tight_layout()
                
                # Save the plot to a BytesIO object
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                plt.close(fig)
                
                # Encode the image to base64
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                
                return base64.b64encode(image_png).decode('utf-8')
            
        except Exception as e:
            # Handle errors gracefully
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating chart {chart_type}: {str(e)}")
            
            # Create a simple error image
            try:
                fig = plt.figure(figsize=(10, 6))
                plt.text(0.5, 0.5, f'Error generating chart: {str(e)}', 
                         horizontalalignment='center', verticalalignment='center',
                         fontsize=14, color='red')
                plt.axis('off')
                
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=100)
                plt.close(fig)
                
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                
                return base64.b64encode(image_png).decode('utf-8')
            except:
                # If even the error image fails, return empty string
                return "" 