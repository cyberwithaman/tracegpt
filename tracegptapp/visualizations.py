import matplotlib
# Use Agg backend to avoid GUI threading issues
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from io import BytesIO
import base64
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, fields, Max, Min
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractHour, ExtractWeekDay
from datetime import datetime, timedelta
from django.utils import timezone
from collections import Counter

from .models import ChatExample, ChatTrace, TraceStep, ContactMessage

# Set plot styling
plt.style.use('ggplot')
sns.set(style="whitegrid")

# Custom color palettes
TAG_COLORS = {
    'correct': '#28a745',
    'misleading': '#ffc107', 
    'incomplete': '#17a2b8', 
    'slow': '#dc3545'
}
STATUS_COLORS = {
    'success': '#28a745',
    'error': '#dc3545',
    'new': '#007bff',
    'in_progress': '#ffc107',
    'completed': '#28a745',
    'spam': '#6c757d'
}

class ModelVisualizations:
    """Class to generate visualizations for all models in the application."""
    
    @staticmethod
    def encode_plot_to_base64(fig=None, close_fig=True):
        """Utility function to convert matplotlib figure to base64 encoded string"""
        if fig is None:
            fig = plt.gcf()
            
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        if close_fig:
            # Safe cleanup for figure to avoid thread issues
            plt.close(fig)
            
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode('utf-8')
    
    @staticmethod
    def safe_cleanup():
        """Safely close all matplotlib figures"""
        try:
            plt.close('all')
        except Exception:
            # Ignore any cleanup errors
            pass
    
    @staticmethod
    def get_model_counts():
        """Generate bar chart showing record count for each model"""
        # Get counts for each model
        chat_examples = ChatExample.objects.count()
        chat_traces = ChatTrace.objects.count()
        trace_steps = TraceStep.objects.count()
        contact_messages = ContactMessage.objects.count()
        
        # Create dataframe for plotting
        df = pd.DataFrame({
            'Model': ['ChatExample', 'ChatTrace', 'TraceStep', 'ContactMessage'],
            'Count': [chat_examples, chat_traces, trace_steps, contact_messages]
        })
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(df['Model'], df['Count'], color=sns.color_palette('viridis', len(df)))
        
        # Add count labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height):,}', ha='center', va='bottom')
        
        ax.set_title('Record Count by Model', fontsize=16)
        ax.set_ylabel('Number of Records')
        ax.grid(axis='y', alpha=0.3)
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def chat_examples_tags_distribution():
        """Generate pie chart of tag distribution for ChatExample model"""
        # Get all chat examples
        examples = ChatExample.objects.all()
        
        if not examples:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, 'No Chat Examples Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
        
        # Collect all tags
        all_tags = []
        for example in examples:
            all_tags.extend(example.tags)
        
        # Count tags
        tag_counts = Counter(all_tags)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = list(tag_counts.keys())
        sizes = list(tag_counts.values())
        colors = [TAG_COLORS.get(tag, '#6c757d') for tag in labels]
        
        # Plot pie chart with percentage and count
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5, 'alpha': 0.8}
        )
        
        # Style the percentage text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Tag Distribution in Chat Examples', fontsize=16)
        # Add legend with counts
        ax.legend([f"{label} ({count})" for label, count in tag_counts.items()], 
                 loc='best', frameon=True, title='Tags')
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def chat_trace_runtime_scatter():
        """Generate scatter plot of ChatTrace runtimes over time with tag coloring"""
        # Get all chat traces
        traces = ChatTrace.objects.all().values('runtime_seconds', 'created_at', 'tags', 'status')
        
        if not traces:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Chat Traces Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Convert to DataFrame
        df = pd.DataFrame(list(traces))
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Sort by date
        df = df.sort_values('created_at')
        
        # Create scatter plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Plot points with different colors based on status
        for status, color in STATUS_COLORS.items():
            status_df = df[df['status'] == status]
            if not status_df.empty:
                ax.scatter(
                    status_df['created_at'], 
                    status_df['runtime_seconds'],
                    color=color,
                    label=status.title(),
                    alpha=0.7,
                    edgecolors='white',
                    s=80
                )
        
        # Add trend line using rolling average
        if len(df) > 1:
            df['rolling_avg'] = df['runtime_seconds'].rolling(
                window=min(5, len(df)), 
                min_periods=1
            ).mean()
            ax.plot(df['created_at'], df['rolling_avg'], 'r--', 
                   label='5-point Rolling Avg', linewidth=2)
        
        # Add labels and styling
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Runtime (seconds)', fontsize=12)
        ax.set_title('Chat Trace Runtime Over Time', fontsize=16)
        
        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        # Add legend
        ax.legend()
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def trace_step_type_boxplot():
        """Generate box plot of runtime distribution by step type"""
        # Get all trace steps
        steps = TraceStep.objects.all().values('step_type', 'runtime_seconds')
        
        if not steps:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Trace Steps Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Convert to DataFrame
        df = pd.DataFrame(list(steps))
        
        # Get step types with at least 2 entries for meaningful boxplot
        step_counts = df['step_type'].value_counts()
        valid_steps = step_counts[step_counts >= 2].index.tolist()
        
        if not valid_steps:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Insufficient data for boxplot', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
        
        # Filter dataframe to include only valid steps
        df_filtered = df[df['step_type'].isin(valid_steps)]
        
        # Create boxplot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create boxplot with seaborn for better styling
        sns.boxplot(
            x='step_type',
            y='runtime_seconds',
            data=df_filtered,
            hue='step_type',  # Use hue parameter to color by step_type
            palette='viridis',
            width=0.6,
            fliersize=5,
            legend=False,  # Don't show legend since it would be redundant
            ax=ax
        )
        
        # Add swarm plot to show individual points
        sns.swarmplot(
            x='step_type',
            y='runtime_seconds',
            data=df_filtered,
            color='black',
            alpha=0.5,
            size=4,
            ax=ax
        )
        
        # Add styling
        ax.set_xlabel('Step Type', fontsize=12)
        ax.set_ylabel('Runtime (seconds)', fontsize=12)
        ax.set_title('Runtime Distribution by Step Type', fontsize=16)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Tight layout to ensure labels fit
        plt.tight_layout()
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def contact_message_status_stacked():
        """Generate stacked bar chart of contact message statuses over time"""
        # Get all contact messages
        messages = ContactMessage.objects.all().values('status', 'created_at')
        
        if not messages:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Contact Messages Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Convert to DataFrame
        df = pd.DataFrame(list(messages))
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Group by month and status
        df['month'] = df['created_at'].dt.to_period('M')
        monthly_status = df.groupby(['month', 'status']).size().unstack(fill_value=0)
        
        # Convert period index to datetime for plotting
        monthly_status.index = monthly_status.index.to_timestamp()
        
        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Get status values that exist in the data
        statuses = [status for status in monthly_status.columns]
        colors = [STATUS_COLORS.get(status, '#6c757d') for status in statuses]
        
        monthly_status.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color=colors,
            width=0.8
        )
        
        # Add styling
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Number of Messages', fontsize=12)
        ax.set_title('Contact Message Status by Month', fontsize=16)
        
        # Format x-axis to show months nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.xticks(rotation=45, ha='right')
        
        # Add legend
        ax.legend(title='Status')
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Tight layout
        plt.tight_layout()
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def weekly_activity_heatmap():
        """Generate heatmap of activity by day of week and hour"""
        # Get all traces
        traces = ChatTrace.objects.all().annotate(
            hour=ExtractHour('created_at'),
            weekday=ExtractWeekDay('created_at')
        ).values('hour', 'weekday')
        
        if not traces:
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No Chat Traces Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Convert to DataFrame
        df = pd.DataFrame(list(traces))
        
        # Create pivot table with weekdays as rows and hours as columns
        activity_pivot = df.pivot_table(
            index='weekday', 
            columns='hour', 
            values='hour', 
            aggfunc='count',
            fill_value=0
        )
        
        # Reindex to ensure all hours are included (0-23)
        all_hours = list(range(24))
        activity_pivot = activity_pivot.reindex(columns=all_hours, fill_value=0)
        
        # Map weekday numbers to names
        weekday_names = {
            1: 'Monday',
            2: 'Tuesday',
            3: 'Wednesday',
            4: 'Thursday',
            5: 'Friday',
            6: 'Saturday',
            7: 'Sunday',
            # Django's ExtractWeekDay might use 0-indexed values on some databases
            0: 'Sunday'
        }
        
        # Reindex to ensure all weekdays are included and in order
        all_weekdays = [day for day in range(1, 8) if day in df['weekday'].unique() or day in range(1, 8)]
        if 0 in df['weekday'].unique():
            all_weekdays = [0] + [d for d in all_weekdays if d != 7]  # Replace 7 with 0 if 0 is Sunday
            
        activity_pivot = activity_pivot.reindex(all_weekdays, fill_value=0)
        
        # Rename index
        activity_pivot.index = [weekday_names[day] for day in activity_pivot.index]
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create heatmap with seaborn
        sns.heatmap(
            activity_pivot,
            cmap='YlGnBu',
            annot=True,
            fmt='g',
            linewidths=0.5,
            ax=ax,
            cbar_kws={'label': 'Number of Traces'}
        )
        
        # Add styling
        ax.set_xlabel('Hour of Day', fontsize=12)
        ax.set_ylabel('Day of Week', fontsize=12)
        ax.set_title('Chat Trace Activity by Day and Hour', fontsize=16)
        
        # Format x-axis to show hours nicely
        ax.set_xticks(np.arange(0, 24, 1))
        ax.set_xticklabels([f'{hour:02d}:00' for hour in range(24)], rotation=45, ha='right')
        
        # Tight layout
        plt.tight_layout()
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def trace_tag_comparison_radar():
        """Generate radar chart comparing performance across different tags"""
        # Use exclude with empty string instead of filter with len__gt
        traces = ChatTrace.objects.exclude(tags=[]).values('tags', 'runtime_seconds')
        
        if not traces:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No Tagged Chat Traces Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Process data for radar chart
        # We'll compute average runtime for each tag
        tag_data = {}
        
        for trace in traces:
            for tag in trace['tags']:
                if tag not in tag_data:
                    tag_data[tag] = {'count': 0, 'total_runtime': 0}
                tag_data[tag]['count'] += 1
                tag_data[tag]['total_runtime'] += trace['runtime_seconds']
        
        # Calculate averages
        for tag in tag_data:
            tag_data[tag]['avg_runtime'] = tag_data[tag]['total_runtime'] / tag_data[tag]['count']
        
        # Prepare data for radar chart
        categories = list(tag_data.keys())
        
        if not categories:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'No Tagged Chat Traces Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
        
        # Values are normalized average runtimes (lower is better)
        max_runtime = max(data['avg_runtime'] for data in tag_data.values())
        values = [(max_runtime - data['avg_runtime']) / max_runtime for tag, data in tag_data.items()]
        
        # Create radar chart
        # We need to close the circle, so we repeat the first value
        categories = categories + [categories[0]]
        values = values + [values[0]]
        
        # Create angles for each category
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
        
        # Create figure
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, polar=True)
        
        # Draw the chart
        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        
        # Set category labels
        ax.set_xticks(angles[:-1])  # Remove the last tick which is a duplicate
        ax.set_xticklabels(categories[:-1])
        
        # Remove y-ticks and add gridlines
        ax.set_yticks([])
        ax.grid(True)
        
        # Add title
        ax.set_title('Performance Comparison by Tag (Higher is Better)', fontsize=16)
        
        # Add legend with actual runtime values
        runtime_legend = [f"{tag}: {data['avg_runtime']:.2f}s" for tag, data in tag_data.items()]
        ax.legend(runtime_legend, loc='best', bbox_to_anchor=(0.9, 0.1))
        
        return ModelVisualizations.encode_plot_to_base64(fig)
    
    @staticmethod
    def examples_vs_traces_correlation():
        """Generate scatter plot comparing number of examples to traces over time"""
        # Get counts by month for both models
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)  # Last year
        
        # Get ChatExample count by month
        examples = ChatExample.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Get ChatTrace count by month
        traces = ChatTrace.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        if not examples and not traces:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No Data Available', 
                   ha='center', va='center', fontsize=14)
            return ModelVisualizations.encode_plot_to_base64(fig)
            
        # Convert to DataFrames
        df_examples = pd.DataFrame(list(examples))
        df_traces = pd.DataFrame(list(traces))
        
        # Handle timezone info
        if not df_examples.empty:
            # Remove timezone info to avoid conversion warnings
            df_examples['month'] = df_examples['month'].dt.tz_localize(None)
        
        if not df_traces.empty:
            # Remove timezone info to avoid conversion warnings
            df_traces['month'] = df_traces['month'].dt.tz_localize(None)
        
        # Create date range for all months
        if not df_examples.empty and not df_traces.empty:
            start_month = min(df_examples['month'].min(), df_traces['month'].min())
            end_month = max(df_examples['month'].max(), df_traces['month'].max())
        elif not df_examples.empty:
            start_month = df_examples['month'].min()
            end_month = df_examples['month'].max()
        else:
            start_month = df_traces['month'].min()
            end_month = df_traces['month'].max()
        
        # Create monthly date range - all naive datetimes
        months = pd.date_range(
            start=start_month.replace(day=1), 
            end=end_month.replace(day=28),
            freq='ME'  # Using 'ME' (month end) instead of deprecated 'M'
        )
        
        # Create DataFrame with all months
        df_all_months = pd.DataFrame({'month': months})
        
        # Merge with data - use concat for timezone safety
        if not df_examples.empty:
            df_examples = pd.concat([
                df_all_months.set_index('month'),
                df_examples.set_index('month')
            ], axis=1).fillna(0).reset_index()
            df_examples.rename(columns={'count': 'example_count'}, inplace=True)
        else:
            df_examples = df_all_months.copy()
            df_examples['example_count'] = 0
        
        if not df_traces.empty:
            df_traces = pd.concat([
                df_all_months.set_index('month'),
                df_traces.set_index('month')
            ], axis=1).fillna(0).reset_index()
            df_traces.rename(columns={'count': 'trace_count'}, inplace=True)
        else:
            df_traces = df_all_months.copy()
            df_traces['trace_count'] = 0
        
        # Combine data
        df_combined = pd.merge(
            df_examples, 
            df_traces, 
            on='month', 
            how='outer'
        )
        
        # Create line chart
        fig, ax1 = plt.subplots(figsize=(12, 7))
        
        # Plot examples on left y-axis
        color = 'tab:blue'
        ax1.set_xlabel('Month', fontsize=12)
        ax1.set_ylabel('Number of Examples', color=color, fontsize=12)
        ax1.plot(df_combined['month'], df_combined['example_count'], 
                 marker='o', color=color, label='Examples')
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Create second y-axis for traces
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Number of Traces', color=color, fontsize=12)
        ax2.plot(df_combined['month'], df_combined['trace_count'], 
                 marker='s', color=color, label='Traces')
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Add title and format x-axis
        fig.suptitle('Examples vs Traces Over Time', fontsize=16)
        fig.autofmt_xdate()
        
        # Add combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Format dates on x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        
        # Add grid
        ax1.grid(True, alpha=0.3)
        
        # Tight layout
        fig.tight_layout()
        
        return ModelVisualizations.encode_plot_to_base64(fig)

# Custom dashboard visualizations for all models
class DashboardVisualizations:
    """Generate visualizations for the admin dashboard."""
    
    @staticmethod
    def get_all_visualizations():
        """Generate all visualizations for the dashboard"""
        try:
            visualizations = {
                'model_counts': ModelVisualizations.get_model_counts(),
                'chat_examples_tags': ModelVisualizations.chat_examples_tags_distribution(),
                'chat_trace_runtime': ModelVisualizations.chat_trace_runtime_scatter(),
                'trace_step_boxplot': ModelVisualizations.trace_step_type_boxplot(),
                'contact_message_status': ModelVisualizations.contact_message_status_stacked(),
                'weekly_activity': ModelVisualizations.weekly_activity_heatmap(),
                'tag_comparison_radar': ModelVisualizations.trace_tag_comparison_radar(),
                'examples_vs_traces': ModelVisualizations.examples_vs_traces_correlation(),
            }
        finally:
            # Ensure all figures are cleaned up properly
            ModelVisualizations.safe_cleanup()
            
        return visualizations 