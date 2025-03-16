# Proctor's Admin Dashboard  (Cheat-Wall)

## Overview

The Proctor's Admin Dashboard is a Flask web application designed for admins and teachers to monitor and manage student examinations. It is a key component of our ecosystem that includes a Python-based desktop application which runs in the background on student computers to monitor user activity. The data collected by the desktop app is sent to this dashboard, where the admin can view detailed logs and risk assessments in real time.

Our solution offers:
- A **Python-based Desktop App** that monitors student activity continuously.
- An **Admin Dashboard** where tests can be created, environments selected, and unique access codes generated and shared with students (similar to Google Classroom).
- A **Dynamic Monitoring Algorithm** that optimizes resource usage by increasing risk only when specific criteria are met.

## Features

- **Automated Proctoring:**  
  The desktop app collects detailed user activity data and submits it securely to the dashboard.

- **Test Management:**  
  Admins/teachers can create tests, select test environments, and share a special test code with students.

- **Dynamic Risk Assessment:**  
  A dynamic algorithm adjusts risk levels based on predefined criteria, ensuring that monitoring resources are utilized only when necessary.

- **Real-Time Monitoring:**  
  All student activity is displayed on the dashboard, allowing administrators to monitor exams in real time and intervene when needed.

- **User-Friendly Interface:**  
  Designed for ease of use, the dashboard provides clear insights and intuitive navigation.

## Ecosystem Overview

- **Desktop Proctoring App:**  
  A Python application running in the background on student machines. It captures activity logs and transmits them to the server.

- **Admin Dashboard (Flask Web App):**  
  Provides a web interface for administrators and teachers to manage tests, view student logs, and analyze risk levels.

- **Dynamic Risk Algorithm:**  
  Evaluates student behavior based on multiple criteria and increases the risk score only when necessary, optimizing monitoring efforts.

## Installation

### Prerequisites

- Python 3.x
- Flask
- Other dependencies listed in `requirements.txt`

### Setup Steps

1. **Clone the Repository:**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
