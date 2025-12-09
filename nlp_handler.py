"""
NLP Handler for Chatbot Integration
Processes natural language commands and generates network topologies
"""

import os
import json
from typing import Dict, Optional
from t5_topology_generator import TopologyInference

class NLPHandler:
    def __init__(self, model_path = os.path.expanduser("~/INDA/VisioGns3/NLP1/trained_topology_model")):
        """
        Initialize NLP handler with topology inference model
        
        Args:
            model_path: Path to trained model
        """
        self.inference_engine = None
        self.model_path = model_path
        self.output_dir = os.path.expanduser("~/INDA/VisioGns3/nlp_outputs")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load model
        self._initialize_model()
    
    def _initialize_model(self):
        """Lazy load the model"""
        try:
            print("🔄 Initializing NLP model...")
            self.inference_engine = TopologyInference(self.model_path)
            print("✅ NLP model ready!")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.inference_engine = None
    
    def process_command(self, user_input: str) -> Dict[str, any]:
        """
        Process user command and generate response
        
        Args:
            user_input: Natural language command from user
            
        Returns:
            Dictionary with status, message, and topology data
        """
        user_input = user_input.strip()
        
        # Check if model is loaded
        if self.inference_engine is None:
            return {
                'status': 'error',
                'message': '❌ Model not loaded. Please check model path.',
                'topology': None
            }
        
        # Detect command type
        command_type = self._detect_command_type(user_input)
        
        if command_type == 'help':
            return self._handle_help()
        elif command_type == 'topology_generation':
            return self._handle_topology_generation(user_input)
        else:
            return self._handle_general_query(user_input)
    
    def _detect_command_type(self, text: str) -> str:
        """Detect the type of command"""
        text_lower = text.lower()
        
        # Help commands
        if any(word in text_lower for word in ['help', 'what can you do', 'commands']):
            return 'help'
        
        # Topology generation keywords
        topology_keywords = [
            'create', 'design', 'build', 'generate', 'topology',
            'network', 'connect', 'pc', 'router', 'switch', 'server'
        ]
        
        if any(keyword in text_lower for keyword in topology_keywords):
            return 'topology_generation'
        
        return 'general'
    
    def _handle_help(self) -> Dict:
        """Return help information"""
        help_text = """
        🤖 <b>Available Commands:</b><br/>
        <ul style='margin-top: 10px; color: #E2E8F0;'>
            <li><b>Topology Generation:</b> Describe a network and I'll create the topology
                <ul style='color: #A0AEC0;'>
                    <li>"Create a network with 3 PCs and a router"</li>
                    <li>"Design a topology with PC1, PC2 connected to RouterA"</li>
                    <li>"Build a simple network with 2 computers and 1 switch"</li>
                </ul>
            </li>
            <li><b>Help:</b> Type "help" to see this message</li>
        </ul>
        """
        
        return {
            'status': 'success',
            'message': help_text,
            'topology': None
        }
    
    def _handle_topology_generation(self, description: str) -> Dict:
        """Generate network topology from description"""
        try:
            print(f"🔮 Processing topology request: {description}")
            
            # Generate topology
            raw_output, parsed_topology = self.inference_engine.predict(description)
            
            # Validate output
            if not parsed_topology['machines']:
                return {
                    'status': 'warning',
                    'message': '⚠️ Could not detect any machines in the topology. Please try rephrasing your request.',
                    'topology': None
                }
            
            # Format output
            formatted_output = self.inference_engine.format_output(parsed_topology)
            
            # Save to file
            output_file = self._save_topology(parsed_topology, description)
            
            # Create response message
            message = f"""
            ✅ <b>Topology Generated Successfully!</b><br/><br/>
            
            <b>📊 Detected Components:</b><br/>
            • <span style='color: #68D391;'>{len(parsed_topology['machines'])} machines</span><br/>
            • <span style='color: #4299E1;'>{len(parsed_topology['connections'])} connections</span><br/><br/>
            
            <b>🖥️ Machines:</b><br/>
            <span style='font-family: monospace; color: #E2E8F0;'>
            {self._format_machines_html(parsed_topology['machines'])}
            </span><br/>
            
            <b>🔗 Connections:</b><br/>
            <span style='font-family: monospace; color: #E2E8F0;'>
            {self._format_connections_html(parsed_topology['connections'])}
            </span><br/>
            
            <span style='color: #A0AEC0;'>💾 Saved to: {output_file}</span>
            """
            
            return {
                'status': 'success',
                'message': message,
                'topology': {
                    'raw': raw_output,
                    'parsed': parsed_topology,
                    'formatted': formatted_output,
                    'file': output_file
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating topology: {e}")
            return {
                'status': 'error',
                'message': f'❌ Error generating topology: {str(e)}',
                'topology': None
            }
    
    def _handle_general_query(self, query: str) -> Dict:
        """Handle general queries"""
        return {
            'status': 'info',
            'message': f"""
            🤔 I'm not sure how to help with that specific request.<br/><br/>
            
            I specialize in <b>network topology generation</b>. Try asking me to:<br/>
            <ul style='color: #A0AEC0;'>
                <li>Create a network topology</li>
                <li>Design a network with specific devices</li>
                <li>Generate connections between machines</li>
            </ul>
            
            Or type <b>"help"</b> for more examples!
            """,
            'topology': None
        }
    
    def _format_machines_html(self, machines: list) -> str:
        """Format machines list for HTML display"""
        if not machines:
            return "<i>None</i>"
        
        lines = []
        for m in machines:
            lines.append(f"  • {m['name']} <span style='color: #63B3ED;'>({m['type']})</span>")
        return "<br/>".join(lines)
    
    def _format_connections_html(self, connections: list) -> str:
        """Format connections list for HTML display"""
        if not connections:
            return "<i>None</i>"
        
        lines = []
        for c in connections:
            lines.append(f"  • {c['source']} → {c['target']} <span style='color: #9F7AEA;'>({c['type']})</span>")
        return "<br/>".join(lines)
    
    def _save_topology(self, topology: Dict, description: str) -> str:
        """Save topology to JSON file"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"topology_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            'timestamp': timestamp,
            'description': description,
            'topology': topology
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath


# Standalone testing
if __name__ == "__main__":
    print("🧪 Testing NLP Handler\n")
    
    handler = NLPHandler(model_path="./NLP1/trained_topology_model")
    
    test_commands = [
        "help",
        "Create a network with 3 PCs connected to a router",
        "What's the weather?",
        "Design a topology with PC1, PC2, and Switch1"
    ]
    
    for cmd in test_commands:
        print(f"\n{'='*80}")
        print(f"Command: {cmd}")
        print('='*80)
        
        result = handler.process_command(cmd)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['topology']:
            print(f"\nTopology File: {result['topology']['file']}")