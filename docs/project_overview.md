# CogniStream Project Overview

## Purpose
CogniStream: Developer Flow-State & Cognitive Load Analytics is a data analytics internship project at Infotact Solutions. It analyses developer work sessions to understand focus, flow-state duration, interruptions, and cognitive load, and presents the results in an interactive dashboard with an AI assistant.

## Dataset
The project uses one file, developer_productivity_dataset.csv. It has 1000 work sessions from 50 developers and 20 original columns. Sessions fall between 2025-01-06 and 2025-10-10 and only on weekdays.

## Important limitations
The dataset comes without official documentation. The source of the data, and whether it is real or synthetic, is not stated. The formulas behind productivity_score and cognitive_load_level are not provided. Results describe associations inside this dataset and must not be read as proof of cause and effect.

## Pipeline
Phase 1 cleans and validates the data without deleting rows. Phase 2 calculates KPIs and charts. Phase 3 is the Streamlit dashboard. Phase 4 is this retrieval-augmented assistant, which answers from project documents and from numbers calculated with Pandas.
