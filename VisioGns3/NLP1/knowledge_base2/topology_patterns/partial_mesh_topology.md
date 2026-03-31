# Partial Mesh Topology

## Description
A partial mesh topology has some devices with multiple connections to other devices, but not all devices are connected to all others. Provides redundancy without full mesh complexity.

## Characteristics
- Some devices have multiple connections
- Not every device connects to every other device
- Provides some redundancy and alternate paths
- More connections than tree, fewer than full mesh
- No fixed pattern - connections vary

## Connection Formula
- Variable: More than (N-1), less than N*(N-1)/2
- Typically 2-4 connections per device on average
- Strategic connections for redundancy

## Keywords
- "partial mesh"
- "redundant"
- "some redundancy"
- "mesh"
- "interconnected"

## Example Patterns
```
5 devices with partial mesh:
  Could have 8-12 connections
  Some devices connect to 2-3 others
  Not all pairs connected
```

## Use Cases
- Redundant networks
- Critical infrastructure
- Balance between cost and reliability
