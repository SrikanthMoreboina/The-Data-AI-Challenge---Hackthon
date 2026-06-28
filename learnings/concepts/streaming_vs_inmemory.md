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

## Our Streaming Implementation

We use a Python generator containing a `yield` statement inside `resume_fetcher.py`:

```python
def stream_candidates(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
```

In Python, `yield` pauses the function execution and returns the current line's candidate dictionary. In the next iteration, Python resumes the function, gets the next line, and garbage collects the previous one. This maintains constant space complexity ($O(1)$) and avoids JVM dependencies.
