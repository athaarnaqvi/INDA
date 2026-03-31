# Full Mesh Topology

## Description
A full mesh topology connects every device to every other device, creating maximum redundancy and fault tolerance.

## Characteristics
- Every device connects to every other device
- Maximum redundancy
- Highest fault tolerance
- Most expensive and complex

## Connection Formula
- For N devices: N*(N-1)/2 connections
- Each device has (N-1) connections

## Keywords
- "full mesh"
- "fully connected"
- "complete mesh"
- "all-to-all"

## Example Patterns
```
3 devices: 1↔2, 1↔3, 2↔3 (3 connections)
4 devices: 1↔2, 1↔3, 1↔4, 2↔3, 2↔4, 3↔4 (6 connections)
5 devices: 10 connections
```

## Use Cases
- Critical systems requiring maximum uptime
- Small networks where cost isn't primary concern
- High reliability requirements
