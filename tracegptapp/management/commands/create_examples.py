from django.core.management.base import BaseCommand
from django.utils import timezone
from tracegptapp.models import ChatExample
import time

class Command(BaseCommand):
    help = 'Populates the database with example data for TraceGPT'

    def handle(self, *args, **options):
        self.stdout.write('Creating example data for TraceGPT...')
        
        # Create chat examples
        examples = [
            {
                'title': 'Simple Greeting',
                'input_prompt': 'Hello! How are you today?',
                'expected_response': 'Hello! I\'m doing well, thank you for asking. How can I assist you today?',
                'tags': ['correct'],
            },
            {
                'title': 'Weather Query',
                'input_prompt': 'What\'s the weather like in New York today?',
                'expected_response': 'I\'m sorry, I don\'t have access to real-time weather information.',
                'tags': ['correct'],
            },
            {
                'title': 'Incomplete Response',
                'input_prompt': 'Can you explain the difference between RAM and ROM?',
                'expected_response': 'RAM is volatile memory used for temporary storage while a computer is running.',
                'tags': ['incomplete'],
            },
            {
                'title': 'Misleading Information',
                'input_prompt': 'Who was the first president of the United States?',
                'expected_response': 'Benjamin Franklin was the first president of the United States.',
                'tags': ['misleading'],
            },
            {
                'title': 'Slow Response',
                'input_prompt': 'Generate a summary of War and Peace by Leo Tolstoy.',
                'expected_response': 'War and Peace is an epic novel by Leo Tolstoy that follows several Russian families during the Napoleonic Wars.',
                'tags': ['slow', 'incomplete'],
            },
        ]
        
        # Clear existing examples
        ChatExample.objects.all().delete()
        
        # Create new examples
        created_count = 0
        for example in examples:
            ChatExample.objects.create(
                title=example['title'],
                input_prompt=example['input_prompt'],
                expected_response=example['expected_response'],
                tags=example['tags'],
                created_at=timezone.now() - timezone.timedelta(days=created_count)  # stagger creation dates
            )
            created_count += 1
            
            # Add a small delay for a nicer display
            time.sleep(0.1)
            self.stdout.write(self.style.SUCCESS(f'Created example: {example["title"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} examples')) 