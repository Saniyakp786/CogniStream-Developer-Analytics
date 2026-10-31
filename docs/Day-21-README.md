\# Day 21 – Flow-State Analysis



\## Project

\*\*CogniStream: Developer Flow-State \& Cognitive Load Analytics\*\*



\## Objective

Analyze developer flow-state duration and understand its relationship with productivity, interruptions, and task types.



\## Work Completed

\- Implemented the Flow-State Analysis page in `dashboard/views.py`.

\- Displayed average flow duration.

\- Calculated the number of sessions with zero flow duration.

\- Analyzed the relationship between flow duration and productivity using Spearman correlation.

\- Created a scatter plot of flow duration versus productivity.

\- Compared flow duration across interruption bands.

\- Visualized the distribution of flow duration.

\- Compared average flow duration across different task types.



\## Key Visualizations

1\. Flow Duration vs Productivity

2\. Flow Duration by Interruption Band

3\. Flow Duration Distribution

4\. Average Flow Minutes by Task Type



\## Testing

\- Added `tests/test\_flow.py`.

\- Verified that the `page\_flow()` function exists and is callable.

\- Test result: \*\*1 passed\*\*.



\## Technologies Used

\- Python

\- Pandas

\- Streamlit

\- Plotly

\- pytest



\## Outcome

The Flow-State Analysis page helps explore how developer focus duration is associated with productivity, interruptions, and task types. These relationships do not necessarily indicate causation.

