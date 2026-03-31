# Network Connection Rules and Constraints

## Hierarchical Connection Patterns

### Standard Network Hierarchy
```
Cloud (Internet/WAN)
  ↓
Router (Core/Edge Layer)
  ↓
Switch (Distribution/Access Layer)
  ↓
End Devices (Servers, PCs, Laptops)
```

### Typical Flow
1. **Cloud → Router**: WAN/Internet entry
2. **Router → Router**: Inter-network routing
3. **Router → Switch**: Distribution to access layer
4. **Switch → Switch**: Redundancy or extended access
5. **Switch → End Devices**: Access layer connectivity
6. **Hub → End Devices**: Legacy access (rare)

## Valid Connection Pairs

### Layer 3 Devices (Routers)
- **Router ↔ Router**: Valid - inter-router connections for routing
- **Router ↔ Switch**: Valid - most common distribution pattern
- **Router ↔ Cloud**: Valid - WAN/Internet connectivity
- **Router ↔ Server**: Valid - direct server connection (less common)
- **Router ↔ Hub**: Valid - legacy configuration

### Layer 2 Devices (Switches)
- **Switch ↔ Switch**: Valid - redundancy, extended access
- **Switch ↔ Router**: Valid - uplink to core
- **Switch ↔ Server**: Valid - most common server connection
- **Switch ↔ PC**: Valid - most common PC connection
- **Switch ↔ Laptop**: Valid - most common laptop connection
- **Switch ↔ Hub**: Valid - legacy extension

### Layer 1 Devices (Hubs)
- **Hub ↔ PC**: Valid - legacy workstation connection
- **Hub ↔ Laptop**: Valid - legacy laptop connection
- **Hub ↔ Server**: Valid - legacy server connection
- **Hub ↔ Switch**: Valid - uplink to better equipment

### End Devices
- **Server ↔ Switch**: Most common
- **Server ↔ Router**: Direct connection (DMZ, special cases)
- **PC ↔ Switch**: Most common
- **PC ↔ Hub**: Legacy
- **Laptop ↔ Switch**: Most common
- **Laptop ↔ Hub**: Legacy

### External Connections
- **Cloud ↔ Router**: Standard WAN/Internet entry point
- **Cloud ↔ Cloud**: Invalid (clouds represent external networks)

## Connection Directionality

### Directional Connections
- Most connections in topology descriptions are **directional**
- Format: `device1 -> device2` means device1 connects TO device2
- In implementation, many are bidirectional for data flow

### Bidirectional Implications
- Physical connections are typically bidirectional
- Data can flow both ways
- In ring/loop topologies, direction matters for token passing

### Special Cases
- **Ring/Loop**: Strictly directional in pattern (1→2→3→...→N→1)
- **Star**: All connections point from center to peripherals
- **Daisy Chain**: Sequential directional (1→2→3→4)
- **Mesh**: Can be bidirectional or specific paths

## Connection Constraints

### Prohibited Patterns
- **End Device ↔ End Device**: Generally not direct
  - PC ↔ PC: No direct connection
  - Server ↔ Server: No direct connection
  - Laptop ↔ Laptop: No direct connection
- **Cloud ↔ End Device**: Clouds don't connect directly to end devices
- **Cloud ↔ Switch**: Typically not direct (goes through router)

### Logical Constraints
- **No Loops** (except ring/loop topology): Tree topologies must be acyclic
- **Single Root**: Tree topologies have one root device
- **Star Center**: Star topology needs exactly one central device
- **Ring Closure**: Ring topology must close (last connects to first)

## Common Network Patterns

### Three-Tier Architecture
```
Core Layer: Routers
  ↓
Distribution Layer: Switches
  ↓
Access Layer: End Devices
```

### DMZ Pattern
```
Internet (Cloud) → Edge Router → DMZ Switch → Public Servers
                              → Internal Network
```

### Redundant Pattern
```
Device A → Primary Path → Device B
        → Backup Path  → Device B
```

## Connection Density Guidelines

### Topology Type vs Connection Count
- **Ring**: N devices = N connections
- **Star**: N peripherals + 1 center = N connections
- **Tree**: N devices ≈ N-1 connections (minimum)
- **Bus**: N devices + 1 bus = N connections
- **Partial Mesh**: N devices = 1.5N to 3N connections (typical)
- **Full Mesh**: N devices = N*(N-1)/2 connections
- **Daisy Chain**: N devices = N-1 connections

## Best Practices

1. **Hierarchical Design**: Follow OSI model layers
2. **Redundancy**: Critical paths should have backups
3. **Scalability**: Design for growth
4. **Simplicity**: Minimize unnecessary complexity
5. **Standards**: Follow industry best practices
