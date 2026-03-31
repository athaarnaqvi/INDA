# Bus/Linear Bus Topology

## Description
A bus topology uses a single backbone (main cable/device) with all other devices connected directly to it. All devices share the same communication medium.

## Characteristics
- Single central backbone/bus
- All devices connect directly to the bus
- One device acts as the bus (router/switch)
- Simple linear structure

## Connection Formula
- For 1 bus + N devices: Exactly N connections
- All connections: Bus → Device

## Keywords
- "bus"
- "linear bus"
- "backbone"
- "using [device] and [N] [devices]"

## Example Patterns
```
1 router + 5 PCs: R→PC1, R→PC2, R→PC3, R→PC4, R→PC5
1 switch + 10 servers: S→S1, S→S2, ..., S→S10
```

## Use Cases
- Simple networks
- Small office setups
- Legacy systems
