# Tree Topology

## Description
A tree topology is a hierarchical structure with a root device at the top, branch devices in the middle, and leaf devices at the bottom. No loops or redundant paths exist.

## Characteristics
- Hierarchical structure: root → branches → leaves
- Root connects to branch devices
- Branch devices connect to leaf devices
- No loops or redundant connections
- Clear parent-child relationships

## Connection Formula
- Varies based on branching factor
- Each branch can have multiple leaves
- No leaf-to-leaf connections

## Keywords
- "tree"
- "hierarchical"
- "root"
- "branches"
- "leaves"
- "as root"
- "as branches"
- "as leaves"

## Example Patterns
```
1 root, 2 branches, 4 leaves:
  Root → Branch1, Root → Branch2
  Branch1 → Leaf1, Branch1 → Leaf2
  Branch2 → Leaf3, Branch2 → Leaf4
```

## Use Cases
- Enterprise networks
- Scalable architectures
- Clear hierarchy needed
