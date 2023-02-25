---
title: Parallel Computing
description: A root page related to information and concepts in the broad category of parallel programming.
---

# Introduction

Parallel computing can take many forms. There is instruction level parallelism, network parallelism, distributed computing, concurrency, etc. This can be generalized.

| Type | Instruction | Data     | Example                             |
|------|-------------|----------|-------------------------------------|
| SISD | Single      | Single   | Sequential execution                |
| MISD | Multiple    | Singe    | Fault-tolerant heterogenous systems |
| SIMD | Single      | Multiple | Vector operations                   |
| MIMD | Multiple    | Multiple | Large distributed systems           |

The above table is known as Flynn's Taxonomy and it was extended at a later date. More in-depth discussion about this can be found at:
- [SISD](SISD.md)
- [MISD](MISD.md)
- [SIMD](SIMD.md)
- [MIMD](MIMD.md)

## Concurrent and Asynchronous

Concurrent programming is the domain of simultaneous access to memory or resources.

-[Memory Consistency Models: A Tutorial](/home/chuck/wiki/files/papers/MemoryConsistencyModels.pdf)
-[Hardware Memory Model](/home/chuck/wiki/files/papers/HardwareMemoryModel.pdf)
-[Programming Languages Memory Model](/home/chuck/wiki/files/papers/ProgrammingLanguagesMemoryModel.pdf)
-[Updating Go's Memory Model](/home/chuck/wiki/files/papers/UpdatingGoMemoryModel.pdf)


## Distributed

## Multi-Process
