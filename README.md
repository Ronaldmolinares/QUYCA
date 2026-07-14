# QUYCA

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-Express-339933?logo=node.js&logoColor=white)
![C++](https://img.shields.io/badge/C++-PlatformIO-00599C?logo=c%2B%2B&logoColor=white)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)
![HTML](https://img.shields.io/badge/Frontend-HTML5-E34F26?logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-TODO-lightgrey)

QUYCA is a computer architecture project focused on wildfire monitoring and early alerting through an embedded + server-based system. The repository combines firmware (C++/PlatformIO), a backend monitoring service (Python), and a web server/dashboard layer (Node.js + static frontend files) to collect, process, and communicate fire-risk events.

The project addresses the need for coordinated fire-event detection and notification workflows by integrating sensing, persistence, and alert channels (including Telegram integration). Its purpose is to provide a practical, educational, and extensible reference implementation for students, instructors, and developers interested in IoT monitoring pipelines and incident-response tooling.

---

## Main Features

### Embedded Monitoring (Microcontroller / Firmware)

- **Sensor-oriented firmware logic**: The `src/main.cpp` module contains the low-level runtime behavior for the embedded device, coordinating hardware interaction and event signaling. This enables deterministic control over the data acquisition cycle and supports near-real-time detection behavior in constrained environments.
- **PlatformIO-based build workflow**: The `platformio.ini` setup indicates a reproducible firmware development environment, simplifying compilation, upload, and device-specific configuration. This benefits contributors by reducing setup friction and ensuring consistent build parameters.
- **Modular firmware extension points**: The presence of `include/` and `lib/` directories follows PlatformIO conventions for reusable components and abstractions, making it easier to scale functionality without tightly coupling all logic into a single source file.

### Monitoring Backend (Python)

- **Fire event monitoring service**: `fire_monitor.py` appears to be the core monitoring process that evaluates incoming data and triggers operational actions when thresholds or event conditions are met. This gives users a centralized fire-state evaluator rather than scattered scripts.
- **Database integration layer**: `database.py` encapsulates data persistence and retrieval responsibilities, separating storage concerns from monitoring logic. This improves maintainability and enables more reliable reporting and auditability of historical events.
- **Structured dependency management**: `requirements.txt` documents the Python runtime dependencies required by backend services, improving environment reproducibility for development and deployment.

### Notification & Messaging (Telegram Integration)

- **Telegram notification module**: `telegram_notifier.py` implements outbound messaging capabilities for operational alerts, enabling fast delivery of high-priority fire incidents to subscribed recipients.
- **Configurable messaging setup**: `telegram_config.py` and `telegram_config.py.example` provide a clear pattern for configuring bot credentials and runtime options. This improves security hygiene by separating templates from real secrets.
- **Automated setup utilities and examples**: `setup_telegram.py`, `telegram_examples.py`, and `test_telegram.py` support validation and onboarding of messaging workflows, which helps developers verify integrations before production use.
- **Dedicated setup documentation**: `TELEGRAM_SETUP.md` and `TELEGRAM_README.md` provide focused operational guidance, reducing configuration errors and accelerating adoption of notification capabilities.

### Web/API Layer (Node.js + Frontend)

- **HTTP server and integration orchestration**: `server.js` acts as the Node.js backend entry point, likely coordinating API endpoints, monitoring-state exposure, and frontend delivery. This centralizes network-facing behavior in one service boundary.
- **Static dashboard assets**: The `public/` directory indicates a web UI delivery layer for visualizing system state and interacting with monitoring workflows. This improves accessibility for operators who need browser-based observability.
- **NPM-based dependency management**: `package.json` and `package-lock.json` provide deterministic JavaScript dependency control, helping teams keep deployments consistent across environments.

### Data Layer

- **Database schema provisioning**: `fire_monitor.sql` provides SQL definitions and initialization logic for the project’s persistence model. This supports predictable bootstrap of required tables and relationships.
- **Separation of schema and application logic**: Keeping SQL provisioning in a dedicated file improves traceability of schema evolution and simplifies environment recreation in local or lab contexts.

### System-Wide

- **Multi-language architecture**: QUYCA combines C++, Python, JavaScript, and HTML, reflecting a layered IoT system where embedded runtime, backend processing, and UI concerns are explicitly separated.
- **Documentation-first operational support**: The repository includes multiple setup and configuration markdown guides, which is valuable for open-source onboarding and academic reproducibility.
- **Extensible project organization**: Conventional folder boundaries (`src`, `include`, `lib`, `test`, and `confrasberry`) make it easier to assign module ownership and evolve the codebase incrementally.

---

## Pages & Views

| View | Description |
|---|---|
| Main Monitoring Dashboard | Primary web interface served from the Node.js layer to inspect monitoring status and system information. |
| Alert/Notification Status View | Section(s) of the web layer related to alert visibility and notification delivery state (implementation details in `public/` are pending explicit mapping). |
| Telegram Integration Setup View | Operational setup flow documented through markdown and scripts for enabling Telegram bot-based alerts. |
| Device/Firmware Runtime View | Embedded runtime behavior represented by firmware logic in `src/main.cpp`; physically observed on device rather than a browser page. |

> **TODO**
> - Enumerate each concrete HTML route/page in `confrasberry/public/` with exact filenames and URL paths.
> - Document API endpoint-to-view mapping once route inventory is extracted from `server.js`.

---

## Execution and Development Guide

### Prerequisites

- **Git** (latest stable)
- **Python 3.x**
- **Node.js + npm** (version compatible with `package.json`)
- **PlatformIO Core** (or PlatformIO IDE extension) for firmware build/upload
- **MySQL / MariaDB** instance (required by SQL schema and backend persistence)
- **Telegram Bot Token and Chat ID** (optional, required for notification features)

---

### Clone repository

```bash
git clone https://github.com/Ronaldmolinares/QUYCA.git
cd QUYCA
```

---

### Backend Setup

The backend logic is located in `confrasberry/` and includes monitoring, database access, and Telegram modules.

```bash
cd confrasberry
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

If the monitoring service is run directly:

```bash
python fire_monitor.py
```

---

### Frontend Setup

The Node.js server and static assets are in `confrasberry/`.

```bash
cd confrasberry
npm install
node server.js
```

> **TODO**
> - Confirm whether the project uses `npm start` / `npm run dev` scripts and document official startup command from `package.json` scripts section.

---

### Database Setup

Initialize the database using the SQL script:

```bash
# Example (adapt host/user/db as needed)
mysql -u <user> -p <database_name> < confrasberry/fire_monitor.sql
```

Ensure database credentials used by the backend match your local DB configuration.

---

### Environment Variables

Create a local environment file for secrets and runtime configuration.

```bash
# from repository root or confrasberry/, depending on your startup convention
cp confrasberry/telegram_config.py.example confrasberry/telegram_config.py
```

For general runtime variables, create a `.env` file in `confrasberry/` if your `server.js` / Python services read from environment variables.

Example template:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=TODO
DB_USER=TODO
DB_PASSWORD=TODO
TELEGRAM_BOT_TOKEN=TODO
TELEGRAM_CHAT_ID=TODO
```

> **TODO**
> - Confirm exact variable names consumed by `database.py`, `fire_monitor.py`, and `server.js`.
> - Add secure secret-management recommendations for production deployment.

---

### Running the project

Recommended local startup order:

1. Start database service (MySQL/MariaDB).
2. Apply `fire_monitor.sql` schema.
3. Run backend monitor (`python fire_monitor.py`).
4. Run Node.js server (`node server.js`).
5. (Optional) Validate Telegram integration (`python test_telegram.py`).

Typical local URLs (subject to project configuration):

- Web UI: `http://localhost:3000` (or configured Node.js port)
- API endpoints: `http://localhost:<server-port>/...`

> **TODO**
> - Confirm actual default port(s) and publish definitive URLs from `server.js` configuration.

---

## Project Structure

```text
QUYCA/
├── .vscode/                         # Editor/workspace settings
├── confrasberry/                    # Main application layer (backend + web + integrations)
│   ├── public/                      # Static frontend assets (HTML/CSS/JS views)
│   ├── node_modules/                # Installed Node dependencies (should generally be gitignored)
│   ├── server.js                    # Node.js HTTP server / API integration entry point
│   ├── package.json                 # Node project metadata and dependencies
│   ├── package-lock.json            # Locked JS dependency graph
│   ├── requirements.txt             # Python dependency manifest
│   ├── fire_monitor.py              # Core fire monitoring workflow/service
│   ├── database.py                  # Database access and persistence logic
│   ├── fire_monitor.sql             # Database schema/bootstrap SQL
│   ├── telegram_notifier.py         # Telegram alert dispatch implementation
│   ├── telegram_config.py           # Runtime Telegram configuration (local secrets/config)
│   ├── telegram_config.py.example   # Telegram configuration template
│   ├── setup_telegram.py            # Setup utility for Telegram integration
│   ├── test_telegram.py             # Telegram integration validation script
│   ├── telegram_examples.py         # Example usage flows for Telegram integration
│   ├── TELEGRAM_SETUP.md            # Telegram setup guide
│   ├── TELEGRAM_README.md           # Telegram integration documentation
│   └── CONFIGURACION_SISTEMA.md     # System configuration guide (Spanish)
├── include/                         # C/C++ header files for firmware modules
│   └── README                       # Notes for include directory usage
├── lib/                             # Reusable C/C++ libraries for firmware
│   └── README                       # Notes for library organization
├── src/                             # Firmware source code
│   └── main.cpp                     # Main embedded application entry point
├── test/                            # Firmware/unit test area
│   └── README                       # Testing guidance for PlatformIO
├── platformio.ini                   # PlatformIO project/build configuration
├── .gitignore                       # Git ignore rules
└── README.md                        # Project documentation
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML + JavaScript (static assets served from `confrasberry/public/`; exact framework not confirmed) |
| Backend | Python 3.x (`fire_monitor.py`, `database.py`) and Node.js (Express-style server in `server.js`) |
| Database | MySQL/MariaDB (schema defined in `confrasberry/fire_monitor.sql`) |
| Authentication | **TODO** (no explicit authentication module identified from current structure scan) |
| Infrastructure | PlatformIO (embedded build toolchain), local runtime services (Python + Node + DB) |
| Testing | Python integration test script (`test_telegram.py`) + PlatformIO `test/` structure |
| DevOps | **TODO** (no CI/CD pipeline files identified in the scanned root structure) |
| Machine Learning | Not identified |
| Desktop | Not identified |
| Mobile | Telegram as messaging channel (client-side consumption via Telegram app, not a native mobile codebase) |

> **TODO**
> - Confirm exact Node.js, Python, and database versions from lockfiles/config and runtime docs.
> - Validate whether Express is explicitly declared and document precise package versions.

---

## Authors

| Name | GitHub |
|---|---|
| Ronald Molinares | [@Ronaldmolinares](https://github.com/Ronaldmolinares) |

---
