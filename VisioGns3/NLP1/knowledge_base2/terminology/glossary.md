# Network Topology Terminology Glossary

## Topology Types

### Ring/Loop Topology
- **Keywords**: ring, loop, circular, ring configuration
- **Pattern**: Devices connected in circular chain
- **Characteristics**: Each device connects to 2 neighbors, closed loop

### Star Topology
- **Keywords**: star, radiating from, hub-and-spoke, centralized
- **Pattern**: Central device with peripherals radiating outward
- **Characteristics**: Single central point, all others connect to it

### Tree Topology
- **Keywords**: tree, hierarchical, root, branches, leaves
- **Pattern**: Hierarchical structure with levels
- **Characteristics**: Root device, branch devices, leaf devices

### Bus Topology
- **Keywords**: bus, linear bus, backbone
- **Pattern**: Single backbone with attached devices
- **Characteristics**: One central device, all others connect to it

### Mesh Topology
- **Keywords**: mesh, fully connected, interconnected
- **Pattern**: All devices connected to all others (full mesh)
- **Characteristics**: Maximum redundancy, highest connection count

### Partial Mesh Topology
- **Keywords**: partial mesh, redundant, some redundancy
- **Pattern**: Some redundant connections, not fully connected
- **Characteristics**: Balance between redundancy and complexity

### Daisy Chain Topology
- **Keywords**: daisy chain, series, sequential, chained
- **Pattern**: Linear sequence without closing loop
- **Characteristics**: Each device connects to next, no return to start

### Hybrid/Mixed Topology
- **Keywords**: hybrid, mixed, heterogeneous, multi-tier
- **Pattern**: Combination of multiple topology types
- **Characteristics**: Flexible, complex, uses multiple patterns

## Device Types

### Router
- **Synonyms**: R, gateway
- **Layer**: Layer 3 (Network)
- **Function**: Routes between networks
- **Naming**: router 1, router 2, etc.

### Switch
- **Synonyms**: SW
- **Layer**: Layer 2 (Data Link)
- **Function**: Forwards frames within network
- **Naming**: switch 1, switch 2, etc.

### Server
- **Synonyms**: SRV, host
- **Layer**: Application (End Device)
- **Function**: Provides services
- **Naming**: server 1, server 2, etc.

### PC
- **Synonyms**: computer, workstation, desktop
- **Layer**: Application (End Device)
- **Function**: User workstation
- **Naming**: pc 1, pc 2, etc.

### Laptop
- **Synonyms**: notebook, portable
- **Layer**: Application (End Device)
- **Function**: Portable workstation
- **Naming**: laptop 1, laptop 2, etc.

### Hub
- **Synonyms**: repeater (though technically different)
- **Layer**: Layer 1 (Physical)
- **Function**: Broadcasts to all ports
- **Naming**: hub 1, hub 2, etc.

### Cloud
- **Synonyms**: WAN, Internet
- **Layer**: External Network
- **Function**: Represents external connectivity
- **Naming**: cloud 1, cloud 2, etc.

## Connection Terminology

### Directional Terms
- **Connected to**: General connection
- **Links to**: Connection between devices
- **Attached to**: Physical connection
- **Wired to**: Physical cabling
- **Points to**: Directional connection

### Structural Terms
- **Root**: Top of hierarchy, starting point
- **Branch**: Intermediate level in hierarchy
- **Leaf**: End point, terminal device
- **Center**: Central point in star topology
- **Peripheral**: Outer devices in star topology
- **Backbone**: Main communication path in bus topology
- **Endpoint**: Terminal device or connection end

### Pattern Terms
- **Sequential**: One after another in order
- **Hierarchical**: Organized in levels/tiers
- **Redundant**: Multiple paths for reliability
- **Centralized**: Organized around central point
- **Distributed**: Spread across multiple devices
- **Meshed**: Interconnected with multiple paths

## Quantity Expressions

### Common Formats
- "X routers" (e.g., "5 routers")
- "with X switches" (e.g., "with 3 switches")
- "using X servers" (e.g., "using 10 servers")
- "having X PCs" (e.g., "having 20 PCs")

### Action Verbs
- **Create**: Build new topology
- **Prepare**: Setup topology
- **Design**: Plan topology
- **Configure**: Setup devices
- **Build**: Construct topology
- **Setup**: Arrange devices
