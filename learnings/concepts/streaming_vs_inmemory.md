# Concept: Streaming vs. In-Memory Processing

When dealing with data files in Python (especially JSON, CSV, or XML exports exceeding 400 MB), developer choices have a huge impact on system stability and runtime.

---

## The Trade-off

| Dimension | In-Memory (Standard) | Streaming (Our Design) |
| :--- | :--- | :--- |
| **RAM Complexity** | $O(N)$ (Scales with candidate count) | $O(1)$ (Constant memory footprint) |
| **Execution Style** | Loads full file into list of dicts | Reads and yields line-by-line |
| **RAM Footprint (100K)**| $\approx 2.4\text{ GB}$ to $3.0\text{ GB}$ | $\approx 50\text{ MB}$ |
| **OOM Risk** | High (crashes if machine runs out of memory) | Extremely Low |
| **Startup Overhead** | High (must parse the entire file first) | Instant (starts processing immediately) |

---

## Why we avoided Apache Spark / Databricks

While Spark is excellent for distributed datasets, utilizing it for this challenge introduces critical engineering issues:

1. **JVM Context Overhead**: Starting a local Spark Context in Python (PySpark) starts a Java Virtual Machine (JVM). This initialization takes **15 to 30 seconds** of setup time.
2. **Docker Dependency Risks**: PySpark requires a Java Runtime Environment (JRE). The sandboxed reproduction container used by judges is a standard Python container. If Java is missing, PySpark crashes immediately.
3. **Scale Inefficiency**: 465 MB of candidate data easily fits into a single CPU core. Spark is designed for multi-gigabyte or terabyte scale; using it on small files introduces unnecessary coordination overhead.

---

## Our Parallel Streaming Implementation

To achieve concurrent processing without losing the low-memory benefits of streaming, we combine standard generators with Python's `multiprocessing.Pool().imap()` streaming map:

```python
def stream_raw_lines(file_path):
    with open_func(file_path) as f:
        for line in f:
            if line.strip():
                yield line

with multiprocessing.Pool(processes=num_cores) as pool:
    results = pool.imap(process_single_candidate, stream_raw_lines(path), chunksize=1000)
    for result in results:
        # Pushes to Min-Heap in the main process
```

* **Why this is optimal**: Instead of reading the full 465MB file into memory or pickling heavy dictionaries, the main process streams **raw text strings** to worker processes. 
* **Lazy Evaluation**: `imap` processes the generator in chunks dynamically. This keeps memory usage bounded to $O(\text{num\_cores} \times \text{chunksize})$ instead of loading all 100K profiles into RAM, while saturating all available CPU cores.

