---
name: devops_engineer
description: Handles containerization, local sandboxing, and offline reproduction recipes using Docker.
---

# DevOps Engineer Skill Guide

This skill directs the DevOps Engineer Agent in building, testing, and verifying isolated, offline runtime environments for candidate ranking reproduction.

---

## 1. Core Objectives
* **Reproducibility**: Ensure the candidate ranker script runs identically on any target system.
* **Isolation**: Prevent dependency conflicts, JVM context delays, or network-bound resource leaks.
* **Security**: Verify that the code runs 100% offline inside sandbox constraints.

---

## 2. Dockerfile Design Pattern
When constructing a `Dockerfile` for Python pipelines, adhere to these practices:

1. **Lightweight Base Image**:
   Use `python:3.11-slim` or `python:3.12-slim` as the base image. Avoid massive full-sized images to reduce pull times, and avoid Alpine if compilation steps are needed (since Alpine lacks glibc).
2. **Offline Boundaries**:
   Ensure no networking components are accessed. Standard libraries only.
3. **Environment Variables**:
   Configure python to not buffer output (`PYTHONUNBUFFERED=1`) and disable writing bytecode (`PYTHONDONTWRITEBYTECODE=1`).
4. **Working Directory & Mount Boundaries**:
   * Set standard path `/app`.
   * Keep outputs ephemeral or mounted via volumes.

---

## 3. Standard Reproduction Commands
Always document a two-step Docker command for reproduction:
1. **Build**:
   `docker build -t redrob-ranker .`
2. **Run (with mounted volumes for input/output)**:
   `docker run -v "${PWD}/outputs:/app/outputs" redrob-ranker --candidates ./datasets/candidates.jsonl --out ./outputs/submission.csv`
