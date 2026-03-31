# Star Topology

## Description
A star topology features a central device (hub/switch/router) with all other devices connected directly to it, radiating outward like spokes on a wheel.

## Characteristics
- One central device
- All peripheral devices connect only to the center
- No direct connections between peripheral devices
- Central point of failure

## Connection Formula
- For 1 central + N peripheral devices: Exactly N connections
- All connections: Central → Peripheral device

## Keywords
- "star"
- "radiating from"
- "hub-and-spoke"
- "centralized"
- "central hub"

## Example Patterns
```
1 center + 3 peripherals: C→1, C→2, C→3
1 switch + 5 servers: S→S1, S→S2, S→S3, S→S4, S→S5
```

## Use Cases
- Most common LAN topology
- Easy to manage and troubleshoot
- Simple to add/remove devices
