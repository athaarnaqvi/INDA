# Daisy Chain Topology

## Description
A daisy chain topology connects devices in a linear sequence, where each device connects to the next one in line, forming a chain without returning to the start.

## Characteristics
- Linear sequence of connections
- Each device connects to the next (except endpoints)
- First device: only 1 connection (to second)
- Last device: only 1 connection (to second-to-last)
- Middle devices: 2 connections each
- NOT a loop (doesn't connect back)

## Connection Formula
- For N devices: (N-1) connections
- Pattern: 1→2, 2→3, 3→4, ..., (N-1)→N

## Keywords
- "daisy chain"
- "series"
- "sequential"
- "linear"
- "chained"
- "in series"
- "daisy-chained"

## Example Patterns
```
4 devices: 1→2, 2→3, 3→4
7 devices: 1→2, 2→3, 3→4, 4→5, 5→6, 6→7
```

## Additional Pattern: Daisy Chain with Endpoints
- Main chain of devices (e.g., routers)
- Each chain device has additional endpoint connections (e.g., servers)
- Creates a spine-and-leaf variation

## Use Cases
- Simple expansion
- Cable cost reduction
- Controlled data flow
