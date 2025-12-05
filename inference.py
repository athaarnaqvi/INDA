"""
Network Topology Inference Module
Generates structured network topology from natural language descriptions
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import re
from typing import Dict, List, Tuple
import os

class TopologyInference:
    def __init__(self, model_path: str = "./NLP1/trained_topology_model"):
        """
        Initialize the topology inference model
        
        Args:
            model_path: Path to the trained model directory
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"🔄 Loading model from {model_path}...")
        print(f"📍 Using device: {self.device}")
        
        # Load base model
        base_model_name = "bigscience/bloom-560m"
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            trust_remote_code=True
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(
            self.model,
            model_path,
            device_map="auto"
        )
        
        self.model.eval()
        print("✅ Model loaded successfully!")
    
    def generate_topology(self, description: str, max_tokens: int = 300) -> str:
        """
        Generate network topology from natural language description
        
        Args:
            description: Natural language description of the network
            max_tokens: Maximum tokens to generate
            
        Returns:
            Structured topology string
        """
        # Format prompt similar to training format
        prompt = f"Extract machines and network connections.\nPrompt: {description}\nResponse:"
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.model.device)
        
        # Generate
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.2,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2
            )
        
        # Decode
        full_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract only the response part (after "Response:")
        if "Response:" in full_text:
            response = full_text.split("Response:", 1)[1].strip()
        else:
            response = full_text
        
        return response
    
    def parse_topology(self, topology_text: str) -> Dict[str, List]:
        """
        Parse the generated topology into structured format
        
        Args:
            topology_text: Generated topology string
            
        Returns:
            Dictionary with 'machines' and 'connections' lists
        """
        result = {
            'machines': [],
            'connections': []
        }
        
        lines = topology_text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if '[MACHINES]' in line.upper() or 'MACHINES:' in line.upper():
                current_section = 'machines'
                continue
            elif '[CONNECTIONS]' in line.upper() or 'CONNECTIONS:' in line.upper():
                current_section = 'connections'
                continue
            
            # Parse machines
            if current_section == 'machines':
                # Format: "PC1 (type=PC)" or "RouterA (type=Router)"
                match = re.match(r'([^\(]+)\s*\(type=([^\)]+)\)', line)
                if match:
                    name, device_type = match.groups()
                    result['machines'].append({
                        'name': name.strip(),
                        'type': device_type.strip()
                    })
                else:
                    # Fallback: just the name
                    name = line.split('(')[0].strip()
                    if name:
                        result['machines'].append({
                            'name': name,
                            'type': 'Unknown'
                        })
            
            # Parse connections
            elif current_section == 'connections':
                # Format: "PC1 -> RouterA (Ethernet)" or "PC1 -> RouterA"
                match = re.match(r'([^\-]+)\s*->\s*([^\(]+)(?:\(([^\)]+)\))?', line)
                if match:
                    source, target, conn_type = match.groups()
                    result['connections'].append({
                        'source': source.strip(),
                        'target': target.strip(),
                        'type': conn_type.strip() if conn_type else 'Ethernet'
                    })
        
        return result
    
    def predict(self, description: str) -> Tuple[str, Dict]:
        """
        Complete prediction pipeline: generate and parse
        
        Args:
            description: Natural language network description
            
        Returns:
            Tuple of (raw_topology_text, parsed_topology_dict)
        """
        print(f"\n📝 Input: {description}")
        print("🔮 Generating topology...")
        
        raw_topology = self.generate_topology(description)
        parsed_topology = self.parse_topology(raw_topology)
        
        print("✅ Generation complete!")
        return raw_topology, parsed_topology
    
    def format_output(self, parsed_topology: Dict) -> str:
        """
        Format parsed topology into clean output
        
        Args:
            parsed_topology: Dictionary with machines and connections
            
        Returns:
            Formatted string representation
        """
        output = []
        
        output.append("[MACHINES]")
        for machine in parsed_topology['machines']:
            output.append(f"{machine['name']} (type={machine['type']})")
        
        output.append("\n[CONNECTIONS]")
        for conn in parsed_topology['connections']:
            output.append(f"{conn['source']} -> {conn['target']} ({conn['type']})")
        
        return '\n'.join(output)


# Example usage and testing
if __name__ == "__main__":
    # Initialize inference engine
    inference = TopologyInference(model_path="./trained_topology_model")
    
    # Test examples
    test_descriptions = [
        "Create a network with 3 PCs connected to a central router via Ethernet",
        "I need a topology with PC1, PC2, and Router1 where both PCs connect to the router",
        "Design a simple network: two computers and one router, all connected",
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING TOPOLOGY INFERENCE")
    print("="*80)
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}")
        print(f"{'='*80}")
        
        raw, parsed = inference.predict(desc)
        
        print("\n📄 Raw Output:")
        print(raw)
        
        print("\n📊 Parsed Structure:")
        print("Machines:", parsed['machines'])
        print("Connections:", parsed['connections'])
        
        print("\n✨ Formatted Output:")
        print(inference.format_output(parsed))