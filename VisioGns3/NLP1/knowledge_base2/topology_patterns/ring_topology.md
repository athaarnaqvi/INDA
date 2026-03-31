# Ring/Loop Topology

## Description
A ring topology connects devices in a circular chain where each device is connected to exactly two neighbors, forming a closed loop.

## Characteristics
- Each device connects to exactly 2 neighbors
- The last device connects back to the first device
- Creates a circular data path
- No central node

## Connection Formula
- For N devices: Exactly N connections
- Connection pattern: Device i → Device (i+1), with Device N → Device 1

## Keywords
- "ring"
- "loop"
- "circular"
- "ring configuration"
- "circular chain"

## Example Patterns
```
3 devices: 1→2, 2→3, 3→1
5 devices: 1→2, 2→3, 3→4, 4→5, 5→1
N devices: 1→2, 2→3, ..., (N-1)→N, N→1
```

## Use Cases
- Token passing networks
- Fault-tolerant systems (can detect breaks)
- Equal access networks
