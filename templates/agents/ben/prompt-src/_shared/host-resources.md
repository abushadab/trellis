Host system resources are limited:

- Local builds, tests, and runtime work together must stay within the CPU limit that the project instructions or runtime guide set. If none is set, use no more than half of the machine's CPUs. When a tool has a setting for jobs, workers, or CPU limits, cap it to match.
- No bulk rebuild, export, or import of unaffected images, and no runtime layout likely to cause very heavy disk writes. Use the smallest affected set, and resume from retained state.
