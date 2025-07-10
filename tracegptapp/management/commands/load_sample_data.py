from django.core.management.base import BaseCommand
from django.utils import timezone
from tracegptapp.models import ChatExample, ChatTrace, TraceStep, ContactMessage
import uuid
import random
import time
import json
from datetime import timedelta

class Command(BaseCommand):
    help = 'Loads sample data for TraceGPT application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading samples',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            ContactMessage.objects.all().delete()
            ChatTrace.objects.all().delete()
            ChatExample.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared successfully'))
        
        self.create_chat_examples()
        self.create_chat_traces_and_steps()
        self.create_contact_messages()
        
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully'))

    def create_chat_examples(self):
        """Create sample chat examples"""
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
            {
                'title': 'Technical Question',
                'input_prompt': 'What is the difference between supervised and unsupervised learning?',
                'expected_response': 'Supervised learning uses labeled data for training, while unsupervised learning identifies patterns in unlabeled data.',
                'tags': ['correct'],
            },
            {
                'title': 'Complex Math Query',
                'input_prompt': 'What is the derivative of f(x) = x^3 + 2x^2 - 5x + 7?',
                'expected_response': 'The derivative of f(x) = x^3 + 2x^2 - 5x + 7 is f\'(x) = 3x^2 + 4x - 5.',
                'tags': ['correct'],
            },
            {
                'title': 'Philosophical Question',
                'input_prompt': 'What is the meaning of life?',
                'expected_response': 'The meaning of life is subjective and varies from person to person based on their values and beliefs.',
                'tags': ['correct'],
            },
        ]
        
        # Clear existing examples
        if ChatExample.objects.count() == 0:
            self.stdout.write('Creating chat examples...')
            
            created_count = 0
            for i, example in enumerate(examples):
                ChatExample.objects.create(
                    title=example['title'],
                    input_prompt=example['input_prompt'],
                    expected_response=example['expected_response'],
                    tags=example['tags'],
                    created_at=timezone.now() - timedelta(days=i)  # stagger creation dates
                )
                created_count += 1
                time.sleep(0.1)  # Small delay for nicer output
                self.stdout.write(f'Created example: {example["title"]}')
                
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} chat examples'))
        else:
            self.stdout.write('Chat examples already exist, skipping...')

    def create_chat_traces_and_steps(self):
        """Create sample chat traces and their steps"""
        if ChatTrace.objects.count() == 0:
            self.stdout.write('Creating chat traces and steps...')
            
            # Get all examples to use as a basis for traces
            examples = list(ChatExample.objects.all())
            if not examples:
                self.stdout.write(self.style.ERROR('No chat examples found, cannot create traces'))
                return
                
            traces_created = 0
            steps_created = 0
            
            # Create traces based on examples
            for example in examples:
                # Create 1-3 traces per example
                for i in range(random.randint(1, 3)):
                    # Create trace
                    trace_run_id = str(uuid.uuid4())
                    runtime = random.uniform(0.5, 3.0)
                    
                    trace = ChatTrace.objects.create(
                        run_id=trace_run_id,
                        input_prompt=example.input_prompt,
                        output_response=example.expected_response,
                        status='success',
                        tags=example.tags,
                        runtime_seconds=runtime,
                        trace_data=self._generate_trace_data(trace_run_id, example.input_prompt, example.expected_response),
                        created_at=timezone.now() - timedelta(hours=random.randint(1, 72))
                    )
                    traces_created += 1
                    
                    # Create steps for each trace
                    step_names = ['preprocess_input', 'generate_response', 'postprocess_response', 'evaluate_response']
                    step_types = ['preprocessing', 'generation', 'postprocessing', 'evaluation']
                    
                    base_time = trace.created_at
                    for j, (step_name, step_type) in enumerate(zip(step_names, step_types)):
                        step_runtime = runtime / (len(step_names) - j * 0.1)  # Distribute runtime across steps
                        start_time = base_time + timedelta(milliseconds=int(j * 200))
                        end_time = start_time + timedelta(milliseconds=int(step_runtime * 1000))
                        
                        TraceStep.objects.create(
                            trace=trace,
                            step_name=step_name,
                            step_type=step_type,
                            input_data=self._generate_step_input(step_type, example.input_prompt if j == 0 else "processed_data"),
                            output_data=self._generate_step_output(step_type, example.expected_response if j == 1 else "processed_output"),
                            start_time=start_time,
                            end_time=end_time,
                            runtime_seconds=step_runtime
                        )
                        steps_created += 1
                        base_time = end_time
            
            self.stdout.write(self.style.SUCCESS(f'Created {traces_created} traces with {steps_created} steps'))
        else:
            self.stdout.write('Chat traces already exist, skipping...')

    def create_contact_messages(self):
        """Create sample contact messages"""
        if ContactMessage.objects.count() == 0:
            self.stdout.write('Creating contact messages...')
            
            names = ['John Smith', 'Emma Johnson', 'Michael Brown', 'Sophia Davis', 
                    'William Wilson', 'Olivia Martinez', 'James Taylor', 'Ava Anderson']
                    
            email_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'example.com']
            
            message_templates = [
                "I'm interested in using TraceGPT for my project. Can you provide more information?",
                "How does TraceGPT handle privacy and data security?",
                "Is there a pricing plan for enterprise usage?",
                "I found a bug in the system. When I try to {}, it shows an error message.",
                "Great tool! I have some feature suggestions I'd like to discuss.",
                "Can you provide technical support for integration with our existing systems?",
                "What kind of export formats do you support for the trace data?",
                "I'm having trouble setting up the local environment. Can you help?"
            ]
            
            statuses = ['new', 'in_progress', 'completed', 'spam']
            status_weights = [0.6, 0.2, 0.15, 0.05]  # Probabilities for each status
            
            created_count = 0
            for i in range(15):  # Create 15 sample messages
                name = random.choice(names)
                email_user = name.lower().replace(' ', '.') + str(random.randint(10, 99))
                email = f"{email_user}@{random.choice(email_domains)}"
                phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
                
                message_template = random.choice(message_templates)
                message = message_template.format(
                    random.choice(['submit a form', 'export data', 'create a new trace', 'filter results'])
                )
                
                # Select status based on weighted probabilities
                status = random.choices(statuses, weights=status_weights, k=1)[0]
                
                # Add notes for some messages
                notes = None
                if status in ['in_progress', 'completed'] and random.random() > 0.5:
                    note_templates = [
                        "Contacted on {date}. Waiting for response.",
                        "Issue resolved by explaining {solution}.",
                        "Referred to technical team on {date}.",
                        "Customer was satisfied with the solution."
                    ]
                    notes = random.choice(note_templates).format(
                        date=(timezone.now() - timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
                        solution=random.choice(['documentation link', 'configuration settings', 'workaround'])
                    )
                
                # Create with a range of dates
                created_date = timezone.now() - timedelta(days=random.randint(0, 30))
                
                ContactMessage.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    message=message,
                    status=status,
                    notes=notes,
                    created_at=created_date,
                    updated_at=created_date + timedelta(hours=random.randint(0, 24) if status != 'new' else 0)
                )
                
                created_count += 1
                self.stdout.write(f'Created message from: {name}')
                
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} contact messages'))
        else:
            self.stdout.write('Contact messages already exist, skipping...')
    
    def _generate_trace_data(self, run_id, input_text, output_text):
        """Generate mock trace data"""
        return {
            "id": run_id,
            "name": "chatbot_interaction",
            "run_type": "chain",
            "start_time": timezone.now().isoformat(),
            "end_time": (timezone.now() + timedelta(seconds=1)).isoformat(),
            "inputs": {"input": input_text},
            "outputs": {"output": {"text": output_text}},
            "metadata": {
                "source": "sample_data",
                "session_id": f"sample-{uuid.uuid4().hex[:8]}"
            }
        }
    
    def _generate_step_input(self, step_type, input_text):
        """Generate mock step input data"""
        if step_type == 'preprocessing':
            return {"raw_input": input_text}
        elif step_type == 'generation':
            return {"processed_input": {"text": input_text, "tokens": len(input_text.split())}}
        elif step_type == 'postprocessing':
            return {"raw_response": input_text}
        else:  # evaluation
            return {"response": input_text}
    
    def _generate_step_output(self, step_type, output_text):
        """Generate mock step output data"""
        if step_type == 'preprocessing':
            return {"processed_input": {"text": output_text, "tokens": len(output_text.split())}}
        elif step_type == 'generation':
            return {"raw_response": output_text}
        elif step_type == 'postprocessing':
            return {"final_response": {"text": output_text, "tokens": len(output_text.split())}}
        else:  # evaluation
            return {
                "evaluation": {
                    "correctness": random.uniform(0.7, 0.95),
                    "relevance": random.uniform(0.7, 0.95),
                    "helpfulness": random.uniform(0.7, 0.95),
                }
            } 