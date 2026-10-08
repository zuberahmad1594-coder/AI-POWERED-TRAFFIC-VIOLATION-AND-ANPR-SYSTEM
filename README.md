\# AI Traffic Violation Sentinel \& Enforcement System



An automated end-to-end edge computer vision and ANPR platform designed to monitor multi-class vehicles, detect traffic infractions in real-time, and automate e-challan generation with photographic evidence.



\## Key Features

\- \*\*Multi-Vehicle Tracking\*\*: Powered by YOLO11 and ByteTrack for cars, motorcycles, buses, and commercial trucks.

\- \*\*Rule Verification Engine\*\*:

&#x20; - Wrong-side / Counter-flow trajectory tracking

&#x20; - Unauthorized stoppage / lane obstruction

&#x20; - Motorcycle triple-riding via rider-area occupancy

&#x20; - Driver \& pillion helmet adherence check

\- \*\*ANPR Pipeline\*\*: EasyOCR engine integrated with Indian license plate positional regex validation and temporal voting consensus.

\- \*\*Adjudication Desk\*\*: Streamlit officer review portal with dynamic filtering, live surveillance playback, and one-click ReportLab PDF e-challan generation.



\## Project Structure

\- `pipeline.py`: Video ingestion, model inference, tracking, ANPR, and SQLite deduplication logger.

\- `violations.py`: Geometric heuristics and spatial vector rules.

\- `challan.py`: ReportLab PDF compiler under Motor Vehicles Act (MVA) sections.

\- `dashboard.py`: Streamlit adjudication portal.

\-

