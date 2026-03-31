# Annotated Topology Examples

This document contains examples of topology descriptions with their structured outputs.

## Example 1: Ring Topology

**Prompt**: 36 routers in a ring configuration.

**Topology Type**: ring

**Device Count**: 36

**Connection Count**: 36

**Machines**: router 1, router 2, router 3, router 4, router 5...

**Sample Connections**:
- router 1 → router 2
- router 2 → router 3
- router 3 → router 4
- router 4 → router 5
- router 5 → router 6
- ... (31 more connections)

---

## Example 2: Tree Topology

**Prompt**: Tree topology with switch 1 as root, 2 hubs as branches, and 4 servers as leaves.

**Topology Type**: tree

**Device Count**: 7

**Connection Count**: 6

**Machines**: switch 1, hub 1, hub 2, server 1, server 2...

**Sample Connections**:
- switch 1 → hub 1
- switch 1 → hub 2
- hub 1 → server 1
- hub 1 → server 2
- hub 2 → server 3
- ... (1 more connections)

---

## Example 3: Star Topology

**Prompt**: 31 servers radiating from switch 1.

**Topology Type**: star

**Device Count**: 32

**Connection Count**: 31

**Machines**: switch 1, server 1, server 2, server 3, server 4...

**Sample Connections**:
- switch 1 → server 1
- switch 1 → server 2
- switch 1 → server 3
- switch 1 → server 4
- switch 1 → server 5
- ... (26 more connections)

---

## Example 4: Partial_Mesh Topology

**Prompt**: partial mesh topology with 19 routers.

**Topology Type**: partial_mesh

**Device Count**: 19

**Connection Count**: 37

**Machines**: router 1, router 2, router 3, router 4, router 5...

**Sample Connections**:
- router 1 → router 10
- router 2 → router 16
- router 3 → router 16
- router 4 → router 14
- router 4 → router 5
- ... (32 more connections)

---

## Example 5: Bus Topology

**Prompt**: Linear bus using router 1 and 43 pcs.

**Topology Type**: bus

**Device Count**: 44

**Connection Count**: 43

**Machines**: router 1, pc 1, pc 2, pc 3, pc 4...

**Sample Connections**:
- router 1 → pc 1
- router 1 → pc 2
- router 1 → pc 3
- router 1 → pc 4
- router 1 → pc 5
- ... (38 more connections)

---

## Example 6: Daisy_Chain Topology

**Prompt**: Daisy-chained routers topology with endpoints.

**Topology Type**: daisy_chain

**Device Count**: 42

**Connection Count**: 41

**Machines**: router 1, router 2, router 3, router 4, router 5...

**Sample Connections**:
- router 1 → router 2
- router 2 → router 3
- router 3 → router 4
- router 4 → router 5
- router 5 → router 6
- ... (36 more connections)

---

## Example 7: Tree Topology

**Prompt**: Three-tier network with 2 routers, 1 switch, and 20 servers.

**Topology Type**: tree

**Device Count**: 23

**Connection Count**: 21

**Machines**: router 1, router 2, switch 1, server 1, server 2...

**Sample Connections**:
- router 1 → switch 1
- switch 1 → server 1
- switch 1 → server 2
- switch 1 → server 3
- switch 1 → server 4
- ... (16 more connections)

---

## Example 8: Tree Topology

**Prompt**: Layered network using 1 router, 2 switches, 18 pcs.

**Topology Type**: tree

**Device Count**: 21

**Connection Count**: 20

**Machines**: router 1, switch 1, switch 2, pc 1, pc 2...

**Sample Connections**:
- router 1 → switch 1
- router 1 → switch 2
- switch 1 → pc 1
- switch 1 → pc 2
- switch 1 → pc 3
- ... (15 more connections)

---

