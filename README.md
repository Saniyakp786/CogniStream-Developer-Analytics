# CogniStream
## Developer Flow-State & Cognitive Load Analytics

### Project Overview
CogniStream is a developer productivity analytics project that studies focus sessions, interruptions, context switching, and estimated cognitive workload.

### Problem Statement
Traditional engineering productivity metrics, such as lines of code and tickets closed, measure output but often overlook interruptions and the difficulty of maintaining focused work.

### Objectives
- Analyze developer activity events.
- Identify uninterrupted flow sessions.
- Measure interruptions and context switching.
- Calculate transparent flow and productivity metrics.
- Visualize insights in an interactive dashboard.

### Technology Stack
- Apache Airflow — workflow orchestration
- ClickHouse — analytical database
- Python and Polars — data processing
- FastAPI — backend API
- React and Tremor.js — frontend dashboard

### Data Sources
Synthetic or authorized event data representing GitHub, Slack, Jira, and IDE activity.

### Project Status
Day 1: Initial project structure and documentation.
