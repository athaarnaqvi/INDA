# Network Topology RAG Knowledge Base

This knowledge base contains reference documents for generating network topologies from natural language descriptions.

## Directory Structure

```
knowledge_base2/
├── topology_patterns/      # Topology type definitions and patterns
├── device_specs/          # Network device specifications
├── connection_rules/      # Connection patterns and constraints
├── terminology/           # Keywords, synonyms, and glossary
└── examples/             # Annotated example topologies
```

## Contents

### Topology Patterns
Reference documents for different network topology types:
- Ring/Loop Topology
- Star Topology
- Tree Topology
- Partial Mesh Topology
- Bus/Linear Bus Topology
- Daisy Chain Topology
- Full Mesh Topology
- Hybrid/Mixed Topology

### Device Specifications
Detailed specifications for network devices:
- Routers (Layer 3)
- Switches (Layer 2)
- Servers (End Devices)
- PCs (End Devices)
- Laptops (End Devices)
- Hubs (Layer 1)
- Clouds (External Networks)

### Connection Rules
Rules and constraints for valid network connections:
- Hierarchical connection patterns
- Valid connection pairs
- Connection directionality
- Prohibited patterns
- Best practices

### Terminology
Keywords, synonyms, and terminology mappings:
- Topology type synonyms
- Device type synonyms
- Connection phrases
- Action verbs
- Quantity extractors

### Examples
Annotated example topologies with:
- Natural language prompts
- Structured machine lists
- Connection specifications
- Topology type classifications

## Usage in RAG System

1. **Query Processing**: User provides natural language topology description
2. **Retrieval**: System retrieves relevant documents based on keywords and patterns
3. **Context Building**: Combines retrieved documents with user query
4. **LLM Processing**: LLM generates structured output (machines + connections)
5. **Validation**: Output validated against connection rules
6. **Pipeline Integration**: Structured data passed to topology generation pipeline

## Document Types

- **Markdown (.md)**: Human-readable reference documentation
- **JSON (.json)**: Machine-readable specifications and rules
- Both formats available for maximum flexibility

## Updating the Knowledge Base

To add new topology types or device specifications:
1. Create new document in appropriate subdirectory
2. Follow existing format and structure
3. Add entries to terminology mappings if needed
4. Update this README with new content

## Integration with LLM

These documents serve as context for the LLM to:
- Understand topology patterns
- Recognize device types and naming conventions
- Apply connection rules and constraints
- Parse natural language descriptions
- Generate valid structured outputs

## Version

Knowledge Base Version: 1.0
Generated: 2025
