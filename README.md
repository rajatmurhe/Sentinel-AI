# 🛡️ SentinelAI: Adaptive Malicious Insider Threat Detection

An end-to-end **cybersecurity research framework and data pipeline** designed to detect and respond to **adaptive insider threats** using a **Bayesian Stackelberg Game**.

Unlike traditional anomaly detection systems that rely on fixed behavioral patterns, SentinelAI models how attackers can change their behavior to avoid detection. It combines **Game Theory, Explainable AI (XAI), and Post-Quantum Cryptography (PQC)** to create an adaptive and secure threat detection environment.

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-20232A?style=flat&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit_Learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-22B5BF?style=flat&logo=react&logoColor=white)
![PQC](https://img.shields.io/badge/Post--Quantum_Cryptography-512BD4?style=flat)
![ML--KEM](https://img.shields.io/badge/ML--KEM-Key_Encapsulation-6A1B9A?style=flat)
![ML--DSA](https://img.shields.io/badge/ML--DSA-Digital_Signatures-8E24AA?style=flat)

<!-- 📸 HERO SCREENSHOT PLACEHOLDER -->
![SentinelAI Main Dashboard](./images/soc-dashboard.png)

---

## 📌 Problem Statement

Traditional insider threat detection often relies on fixed behavioral patterns, but attackers can **change their tactics to avoid detection**.

SentinelAI models the attacker-defender interaction as a **dynamic Stackelberg Game** using **RASRO (Risk-Adaptive Security Response Optimization)**. It uses historical interactions, attacker adaptation, and defense effectiveness to select appropriate security responses.

> **Adaptive insider threat detection using Game Theory, Explainable AI, and Post-Quantum Cryptography.**

---

## Key Features

### 1. Dynamic Stackelberg Game Engine — RASRO

- Models **SOC (Leader)** and **Insider (Follower)** interactions using historical PostgreSQL data.
- Calculates **AAS** and **RES** to track attacker adaptation and defense effectiveness.
- Supports adaptive actions such as `REVOKE_SESSION` and `RESTRICT_ACCESS`.

### 2. Explainable AI (XAI)

- Uses **Isolation Forest** and **One-Class SVM** to detect unusual behavior.
- **Tree SHAP** explains which features contributed to each anomaly decision.

### 3. Post-Quantum Cryptography (PQC)

- **ML-KEM** for secure post-quantum key establishment.
- **ML-DSA** for signing security decisions and audit records.

> **ML-KEM → ML-DSA → Signed Decision → PostgreSQL Audit**

### 4. Interactive Ablation Simulator

- React-based multi-cycle attack simulation with **Massive Exfiltration** and **Stealth Evasion** scenarios.
- Visualizes **AAS, RES, attacker adaptation, and defense response**, comparing static and adaptive detection.

---

## Platform Screenshots

### Secure Access Portal

> Role-based login system that protects access to the SOC dashboard and backend resources.

<!-- 📸 LOGIN SCREENSHOT -->
![Secure Login](./images/login-page.png)

### Executive SOC Dashboard

> Displays incoming telemetry, active security incidents, anomaly scores, and Tree SHAP feature attribution.

<!-- 📸 SOC DASHBOARD SCREENSHOT -->
![Executive SOC Dashboard](./images/soc-dashboard.png)

### Adaptive Attacker Simulator

> Allows users to run multi-cycle attack simulations using custom telemetry or predefined scenarios such as **Massive Exfiltration** and **Stealth Evasion**.

<!-- 📸 SIMULATOR SCREENSHOT -->
![Threat Simulator Input](./images/threat-simulator.png)

### Research Ablation Study & Time-Series Graphs

> Displays how the **Attacker Adaptation Score (AAS)** and **Response Effectiveness (RES)** change across multiple attack turns.

<!-- 📸 GRAPHS SCREENSHOT -->
![Ablation Study Graphs](./images/ablation-graphs.png)

### ML-KEM & ML-DSA Post-Quantum Cryptography

> Terminal demonstration showing the ML-KEM key encapsulation process and ML-DSA digital signature generation and verification.

<!-- 📸 PQC TERMINAL SCREENSHOT -->
![ML-KEM and ML-DSA Terminal](./images/pqc-terminal.png)

### Cryptographic Audit Ledger

> Displays the historical record of telemetry events, anomaly decisions, and Stackelberg mitigation actions.

<!-- 📸 AUDIT SCREENSHOT -->
![Audit Telemetry](./images/audit-telemetry.png)

### End-to-End Decision & Enforcement Workflow

> End-to-end flow showing how telemetry moves through anomaly detection, XAI analysis, RASRO evaluation, mitigation decision, cryptographic protection, and enforcement.

<!-- 📸 END-TO-END WORKFLOW FLOWCHART -->
![End-to-End Decision and Enforcement Workflow](./images/end-to-end-workflow.png)

### 🏗️ System Architecture

> High-level architecture showing the interaction between the frontend, backend services, machine learning pipeline, RASRO engine, PostgreSQL database, and post-quantum cryptography layer.

<!-- 📸 ARCHITECTURE IMAGE -->
![SentinelAI System Architecture](./images/architecture.png)

---
## ⚙️ Architecture Components

The system is organized into a complete pipeline covering data collection, anomaly detection, explainability, game-theoretic decision making, security enforcement, post-quantum protection, and audit storage.

### Core Components

- **Backend:** FastAPI + SQLAlchemy for REST APIs, application logic, and database management.
- **Database:** PostgreSQL for telemetry, historical interaction states, and audit records.
- **Machine Learning:** Isolation Forest + One-Class SVM for anomaly detection, with SHAP for explainability.
- **Game Engine:** RASRO-based Stackelberg evaluation for adaptive attacker-defender interactions.
- **PQC Layer:** ML-KEM for key encapsulation and ML-DSA for digital signatures.
- **Frontend:** React 18 + Tailwind CSS + Recharts for the SOC dashboard, simulations, and visualizations.
- **Enforcement:** Adaptive security actions such as monitoring, step-up authentication, access restriction, and access revocation.
- **Audit & Feedback:** Stores decisions and enforcement outcomes while feeding new behavioral data back into the system.

### Post-Quantum Security Layer

The PQC layer contains two main components:

**ML-KEM**
- Used for secure key encapsulation and key establishment.
- Provides post-quantum protection for cryptographic key exchange.

**ML-DSA**
- Used for digital signatures.
- Signs security decisions and audit records.
- Allows the system to verify that records have not been modified after signing.

---

## Stackelberg Research Metrics

| Metric | Range | Description | Game Theory Role |
| :--- | :---: | :--- | :--- |
| **AAS** | `-1.0` to `1.0` | **Attacker Adaptation Score:** Measures how much the attacker's strategy changes. | Helps identify strategy changes such as **Aggressive → Stealth** behavior. |
| **RES** | `-1.0` to `1.0` | **Response Effectiveness:** Measures how well the SOC's previous action handled the current threat. | Helps determine whether actions such as **Revoke** or **Restrict** were effective. |

---

## PQC Security Flow

    Security Decision
           │
           ▼
       RASRO Engine
           │
           ▼
      Mitigation Action
           │
           ├──────────────► ML-KEM
           │                    │
           │                    ▼
           │             Secure Key Establishment
           │
           ▼
         ML-DSA
           │
           ▼
      Digital Signature
           │
           ▼
     Signed Audit Record
           │
           ▼
       PostgreSQL

---

## 🚀 Getting Started

### Prerequisites

- 🐍 Python 3.10+
- 🟢 Node.js v18+
- 🐘 PostgreSQL v15+

### 1. 🗄️ Database Setup

Create a local PostgreSQL database named:

`sentinelai_db`

Update the database URL in `backend/.env`:

`DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/sentinelai_db`

### 2. ⚡ Backend Installation

`cd backend`

`python -m venv venv`

**Windows:**

`venv\Scripts\activate`

**macOS/Linux:**

`source venv/bin/activate`

Install the dependencies:

`pip install -r requirements.txt`

Start the FastAPI server:

`uvicorn app.main:app --reload --port 8000`

The backend will start on:

`http://localhost:8000`

### 3. ⚛️ Frontend Installation

Open a new terminal and run:

`cd frontend`

`npm install`

Start the React dashboard:

`npm start`

The SOC Dashboard will be available at:

`http://localhost:3000`

From the dashboard, navigate to the **Threat Simulator** tab to run the attack simulations and ablation studies.

---

## 🧩 Project Structure

    SentinelAI/
    │
    ├── backend/
    │   ├── app/
    │   │   ├── api/
    │   │   ├── core/
    │   │   │   ├── pqc_kem.py
    │   │   │   └── pqc_dsa.py
    │   │   ├── models/
    │   │   └── services/
    │   ├── requirements.txt
    │   └── ...
    │
    ├── frontend/
    │   ├── src/
    │   ├── package.json
    │   └── ...
    │
    └── README.md

---

## 🔬 Research Focus

SentinelAI brings together several areas of cybersecurity and AI:

- 🎮 **Game Theory** — Modeling attacker-defender interactions through Stackelberg games and RASRO.
- 🤖 **Machine Learning** — Detecting unusual user behavior using Isolation Forest and One-Class SVM.
- 🔎 **Explainable AI** — Understanding why an event was flagged using Tree SHAP.
- 🎯 **Adaptive Threat Modeling** — Tracking how attackers change their behavior across multiple interactions.
- 🔐 **Post-Quantum Cryptography** — Using ML-KEM for key establishment and ML-DSA for digital signatures.
- 🛡️ **Security Enforcement** — Connecting threat evaluation to actions such as session revocation and access restriction.
- 📊 **Data Visualization** — Analyzing attacker adaptation and defensive response through interactive dashboards and time-series graphs.

The goal is to provide a practical research platform for studying **adaptive insider threats** by combining **Game Theory, Machine Learning, Explainable AI, and Post-Quantum Cryptography** in a single security workflow.
