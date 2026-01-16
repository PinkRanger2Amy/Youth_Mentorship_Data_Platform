# Youth_Mentorship_Data_Platform
Built a Python and PostgreSQL data platform that ingests mentor and mentee applications from online forms, stores raw and normalized data, and automatically matches mentors to mentees based on shared interests using a scoring algorithm.

Youth Mentorship Data Platform (Data Analytics Focus)

A data analytics project that transforms online mentorship applications into a structured PostgreSQL database and generates insight-driven mentor–mentee matches using Python.

This project emphasizes data ingestion, cleaning, normalization, and analysis-ready design.

📊 Data Analytics Focus

This project was designed with a data analyst mindset, focusing on:

Converting raw form data into structured tables

Preserving original submissions for auditability

Creating clean, queryable datasets

Supporting analysis and reporting through SQL

Enabling data-driven matching decisions

🧱 Data Stack

Python (ETL & data processing)

Pandas (data cleaning & transformation)

PostgreSQL (relational analytics database)

SQLAlchemy (database access)

Docker (reproducible data environment)

Google Forms (data collection)

🗂️ Analytical Data Model
Table	Purpose
mentors	Clean mentor dataset
mentees	Clean mentee dataset
mentor_intake_submissions	Raw mentor form data (JSON)
mentee_intake_submissions	Raw mentee form data (JSON)
matches	Analytical match results with scores

This design supports trend analysis, program reporting, and future dashboards.

📈 Example Analyst Queries
-- Total mentors and mentees
SELECT COUNT(*) FROM mentors;
SELECT COUNT(*) FROM mentees;

-- Top matches by score
SELECT * FROM matches
ORDER BY match_score DESC;

-- Interest-based insights
SELECT interests, COUNT(*)
FROM mentors
GROUP BY interests;



<img width="1296" height="649" alt="Screenshot 2026-01-16 at 2 27 50 PM" src="https://github.com/user-attachments/assets/7f4ac883-c7ec-4123-a443-ac0ca3a1bcbb" />


<img width="1296" height="649" alt="Screenshot 2026-01-16 at 2 27 50 PM" src="https://github.com/user-attachments/assets/25b1dbc2-112e-4564-be6d-003e9dda5d04" />



🧠 Analyst TakeawaysDesigned a repeatable ETL pipeline

Cleaned and normalized real-world form data

Preserved raw data for validation and reprocessing

Built analysis-ready tables for reporting




Applied scoring logic to support decision-making
