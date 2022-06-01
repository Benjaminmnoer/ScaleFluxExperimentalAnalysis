1. Goal
To quantify performance characteristics of the ScaleFlux device. Under here is throughput, response time etc.
Multiple articles comes with different claims. We want to prove/disprove these from the results of these experiments.

Specifically we have two goals:
- Is there a throughput gain in moving the compression from the CPU to the ScaleFlux device?
    - Under which circumstances does the ScaleFlux device perform the best?
- Is there an improved storage utilization when moving the compression from the CPU to the ScaleFlux device?
    - Under which circumstances does the ScaleFlux device perform the best?
- Does the IO storage stack change for a specialized device like ScaleFlux (Include as a goal in Experimental Design)

2. System
server with scaleflux device
Intel 20 core system (4 efficiency cores)

3. Metric
Throughput 
- MB/s
- IOps (FIO)
- Transactions/s (RocksDB)

Response time
- Completion latency
- Device latency
- Queue latency? (FIO with direct I/O does not measure this, as the commands are directly issued to the driver)

Compression
- Logical data written
- Physical data written
- Ratio of logical/physical

CPU
- Utilization
- Cache misses  

4. Workload
Fio for micro benchmark
- I/O engine: libaio and io_uring
- Direct I/O: On
- Patterns
    - Random fill to point x  # To reach our common state between experiments
    - Read/Write random LBA's # Somewhat realistic usecase
    - Overwrite same LBA      # To stress test the FTL, especially the mapping and garbage collection.
    - Overwrite ranges of LBA # To stress test the FTL, especially the mapping and garbage collection.

RocksDB for macro benchmark with db_bench
- Compression engine: zlib # Due to ScaleFlux running zlib
- I/O engine: io_uring is possible, perhaps libaio aswell
- Patterns
    - fillrandom # To reach our common state between experiments
    - overwrite
    - readwhilewriting

5. Parameters and Levels
Fio
- block size = seq { for i in 1 .. 10 -> (2k^i) }
    - To see if the ftl favors any block size. We expect no favorite, since there might be no internal page alignment constraint.
- parallelism level = 1 thread to 20 - The number of cores on the machine. What about efficiency cores?
    - To see how well the device handles multiple requests, especially with regard to compression
- io depth = how relevant is this? Fix to 16 or vary?
    - Assuming this means some kind of batching, this helps saturating the device?
- Compression ratio of input data = take low and high values?
    - More compressible data should reduce throughput, due to the need for more computations in the device.

RocksDB
- Place of Compression = In rocksdb vs in scaleflux
    - Is it more beneficial to move compression to the data path, especially with regard to transactions / s
- Compression ratio of input data = take low and high values?
    - As above, more compressible data should reduce throughput
- Parallelism level = 1 thread to 20 - The number of cores on the machine. What about efficiency cores?
    - As above.

6. Experimental constants?
Repetitions= multiple runs or more I/O counts
I/O count = derived from startup phase experiment
Initial state = Completely write vs. partitioned write

target_storage ['scaleflux', ...]
run_types = ['sequential-fill', 'sequential-read', 'random-write', 'random-read']
block_size = seq { for i in 1 .. 10 -> (2k^i) } //Increments of 2k
repetition = 5

RUNTIME PARAMETERS PLAY AROUND TO FIND WARMUP AND COOLDOWN TIME:
time_based = true
run_time = 10 minutes? (at least 90% of meaningful/consistent data)
ramp_Time = 30 sec? (warm up time)
time_based = 1
repetition = 5


Total time for all experiments for a single type: 50 minutes
Total combination: 4*10*xx WHERE xx = target_storages
40*50 min = 2000 min. 
33 hours? Too fast? Maybe increase the parameters.