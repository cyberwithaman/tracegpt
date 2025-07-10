"""
LangSmith utilities for tracing and evaluating chatbot responses
"""
import uuid
import time
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from langsmith import Client
from langsmith.run_trees import RunTree

class TracerManager:
    """
    Utility class to manage LangSmith tracing for chatbot interactions
    """
    
    def __init__(self):
        # Initialize LangSmith client
        self.client = Client(
            api_key=settings.LANGSMITH_API_KEY if settings.LANGSMITH_API_KEY else None
        )
        # Set project name
        self.project_name = settings.LANGSMITH_PROJECT
        # Store our child runs separately since RunTree is immutable
        self.children_map = {}
        
    def _prepare_json_data(self, data):
        """Convert data to JSON serializable format"""
        if data is None:
            return None
            
        if isinstance(data, dict):
            return {k: self._prepare_json_data(v) for k, v in data.items()}
            
        if isinstance(data, list):
            return [self._prepare_json_data(item) for item in data]
            
        if isinstance(data, (uuid.UUID, datetime)):
            return str(data)
            
        # Handle timezone-aware datetime objects
        if hasattr(data, 'isoformat'):
            return data.isoformat()
            
        # Return primitive types as-is
        return data
    
    def start_trace(self, input_prompt, metadata=None):
        """Start a new trace for a chatbot interaction"""
        run_id = str(uuid.uuid4())
        
        # Create the root run tree
        run_tree = RunTree(
            name="chatbot_interaction",
            run_type="chain",
            inputs={"input": input_prompt},
            run_id=run_id,
            serialized={
                "name": "TraceGPT Chatbot Interaction",
                "metadata": metadata or {},
            },
            project_name=self.project_name
        )
        
        # Initialize the children list for this run_id
        self.children_map[run_id] = []
        
        return run_tree
    
    def add_step(self, run_tree, step_name, step_type, inputs=None, outputs=None, start_time=None, end_time=None):
        """Add a step to the trace"""
        if start_time is None:
            start_time = timezone.now()
            
        if end_time is None:
            end_time = timezone.now()
        
        # Create a new child RunTree directly
        child_run_id = str(uuid.uuid4())
        
        # Ensure inputs and outputs are properly serializable
        safe_inputs = self._prepare_json_data(inputs or {})
        safe_outputs = self._prepare_json_data(outputs or {})
        
        child_run = RunTree(
            name=step_name,
            run_type=step_type,
            inputs=safe_inputs,
            outputs=safe_outputs,
            start_time=start_time,
            end_time=end_time,
            run_id=child_run_id,
            parent_run_id=run_tree.id,
            serialized={
                "name": step_name,
                "type": step_type,
            },
            project_name=self.project_name
        )
        
        # Store the child run in our map
        if run_tree.id in self.children_map:
            self.children_map[run_tree.id].append(child_run)
        else:
            self.children_map[run_tree.id] = [child_run]
        
        return child_run
        
    def process_input(self, run_tree, input_text):
        """Mock preprocessing step"""
        start_time = timezone.now()
        time.sleep(0.2)  # Simulate processing time
        
        # Simulate preprocessing
        processed_input = {
            "text": input_text,
            "tokens": len(input_text.split()),
            "processed_at": timezone.now().isoformat()
        }
        
        end_time = timezone.now()
        
        child = self.add_step(
            run_tree=run_tree,
            step_name="preprocess_input",
            step_type="preprocessing",
            inputs={"raw_input": input_text},
            outputs={"processed_input": processed_input},
            start_time=start_time,
            end_time=end_time
        )
        
        return processed_input
        
    def generate_response(self, run_tree, processed_input):
        """Mock response generation step"""
        start_time = timezone.now()
        time.sleep(0.5)  # Simulate thinking time
        
        input_text = processed_input["text"]
        
        # Very simple mock response generator
        if "hello" in input_text.lower():
            response = "Hello! How can I assist you today?"
        elif "help" in input_text.lower():
            response = "I'm here to help. What do you need assistance with?"
        elif "weather" in input_text.lower():
            response = "I'm sorry, I don't have access to real-time weather information."
        elif "name" in input_text.lower():
            response = "My name is TraceGPT, a demonstration chatbot for tracing interactions."
        else:
            response = "I understand your message, but I'm just a simple mock chatbot for demonstration purposes."
        
        end_time = timezone.now()
        
        child = self.add_step(
            run_tree=run_tree,
            step_name="generate_response",
            step_type="generation",
            inputs={"processed_input": processed_input},
            outputs={"raw_response": response},
            start_time=start_time,
            end_time=end_time
        )
        
        return response
        
    def postprocess_response(self, run_tree, response_text):
        """Mock postprocessing step"""
        start_time = timezone.now()
        time.sleep(0.2)  # Simulate processing time
        
        # Simulate postprocessing
        processed_response = {
            "text": response_text,
            "tokens": len(response_text.split()),
            "processed_at": timezone.now().isoformat()
        }
        
        end_time = timezone.now()
        
        child = self.add_step(
            run_tree=run_tree,
            step_name="postprocess_response",
            step_type="postprocessing",
            inputs={"raw_response": response_text},
            outputs={"final_response": processed_response},
            start_time=start_time,
            end_time=end_time
        )
        
        return processed_response
        
    def end_trace(self, run_tree, final_output):
        """End the trace and save results"""
        # Create a dictionary for our final trace data
        trace_data = {
            "id": str(run_tree.id),
            "name": run_tree.name,
            "run_type": run_tree.run_type,
            "start_time": run_tree.start_time.isoformat() if run_tree.start_time else None,
            "end_time": timezone.now().isoformat(),
            "inputs": self._prepare_json_data(run_tree.inputs),
            "outputs": {"output": self._prepare_json_data(final_output)},
            "children": []
        }
        
        # Add children from our map
        child_runs = self.children_map.get(run_tree.id, [])
        for child in child_runs:
            child_data = {
                "id": str(child.id),
                "name": child.name,
                "run_type": child.run_type,
                "start_time": child.start_time.isoformat() if child.start_time else None,
                "end_time": child.end_time.isoformat() if child.end_time else None,
                "inputs": self._prepare_json_data(child.inputs),
                "outputs": self._prepare_json_data(child.outputs),
            }
            trace_data["children"].append(child_data)
        
        return trace_data
        
    def evaluate_response(self, run_tree, response, expected=None):
        """Mock evaluation of the response"""
        start_time = timezone.now()
        time.sleep(0.3)  # Simulate evaluation time
        
        # Very simple evaluation (in a real system, this would be more sophisticated)
        evaluation = {
            "correctness": 0.8,
            "relevance": 0.75,
            "helpfulness": 0.7,
            "overall_score": 0.75
        }
        
        if expected:
            # Compare with expected response
            common_words = set(response.lower().split()) & set(expected.lower().split())
            similarity = len(common_words) / max(len(set(response.lower().split())), len(set(expected.lower().split())))
            evaluation["similarity_to_expected"] = similarity
        
        end_time = timezone.now()
        
        child = self.add_step(
            run_tree=run_tree,
            step_name="evaluate_response",
            step_type="evaluation",
            inputs={"response": response, "expected": expected},
            outputs={"evaluation": evaluation},
            start_time=start_time,
            end_time=end_time
        )
        
        return evaluation
        
    def get_children(self, run_id):
        """Get children for a run"""
        return self.children_map.get(run_id, []) 