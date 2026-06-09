<div align="center">

# 📁 Digital Asset Management System

**A full-stack, role-based platform for managing digital creative assets across projects — built with Flask, Streamlit, MySQL, and ImageKit.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![ImageKit](https://img.shields.io/badge/ImageKit-CDN%20Storage-009AF8?style=for-the-badge)](https://imagekit.io)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [User Roles & Capabilities](#-user-roles--capabilities)
- [File Lifecycle](#-file-lifecycle)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Reference](#-api-reference)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌐 Overview

The **Digital Asset Management System (DAM)** is a multi-role web application designed to streamline the lifecycle of digital creative assets — images, videos, audio, and documents — within client projects.

It implements a structured, approval-based workflow:

> **Client** creates a project → **Admin** assigns a Project Manager → **PM** assigns Employees → **Employees** upload and revise assets → **Client** reviews and approves final files.

This project was built as a full-stack DBMS application demonstrating:
- Role-based access control (RBAC)
- MySQL transactions and rollback safety
- File versioning with cloud storage
- Audit logging via database triggers
- Storage quota enforcement

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Role-Based Access** | Four distinct roles — Admin, Project Manager, Employee, Client — each with their own dashboard and permissions |
| 📂 **Project Management** | Clients create projects with auto-generated folder structures (Images, Videos, Audio, Others) |
| 📤 **Cloud File Storage** | Real file uploads to **ImageKit CDN**; CDN URLs stored in the database |
| 🔢 **File Versioning** | Full version history per file; employees can upload revised versions |
| ✅ **Approval Workflow** | Clients approve or reject submitted file versions with feedback comments |
| 💾 **Storage Quota Tracking** | Per-user storage limits enforced on every upload via DB triggers |
| 🔄 **MySQL Transactions** | Atomic operations for project creation and employee assignment with full rollback support |
| 📋 **Audit Logging** | Every file status change is recorded in a `File_Status_Log` table (via DB trigger) |
| 👥 **Employee Assignment Rules** | A PM can assign an employee to at most **2 projects**; duplicate assignment is prevented atomically |
| 🧪 **Transaction Simulator** | Interactive demo (in PM dashboard) showing how concurrent operations are safely handled |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Browser (Streamlit UI)                  │
│                     localhost:8501                       │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP REST
┌─────────────────────▼───────────────────────────────────┐
│              Flask REST API Backend                      │
│                 localhost:5000                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ /admin   │ │ /client  │ │  /pm     │ │ /employee │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │          /project   /file   /comments              │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────┬───────────────────┘
               │ mysql-connector      │ REST API (Basic Auth)
┌──────────────▼──────┐   ┌───────────▼──────────────────┐
│   MySQL Database    │   │        ImageKit CDN           │
│   dam_system        │   │  ik.imagekit.io/harshit2407   │
└─────────────────────┘   └──────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Backend API** | Python + Flask | 3.1.3 |
| **Frontend UI** | Python + Streamlit | Latest |
| **Database** | MySQL | 8.x |
| **File Storage** | ImageKit CDN | SDK v5.2.0 |
| **DB Connector** | mysql-connector-python | 9.6.0 |
| **HTTP Client** | requests / httpx | Latest |

---

## 👥 User Roles & Capabilities

### 🛠 Admin
- View storage usage statistics for all users
- Assign Project Managers to projects
- Monitor all active projects and their current status
- View the full audit log of file status changes

### 🧑‍💼 Project Manager
- View projects assigned to them
- Assign employees to projects (enforced: max 2 projects per employee)
- Review in-process files and add feedback comments
- Run the **Transaction Simulator** to demo concurrency safety

### 🧑‍💻 Employee
- View assigned projects and their file/folder structure
- Upload new files to ImageKit (starts as `In-Process`)
- Upload new versions of existing files
- Delete own non-approved versions
- View version history and PM/client comments

### 👤 Client
- Create new projects (auto-creates Root + Images/Videos/Audio/Others folders)
- Upload initial raw assets to ImageKit (starts as `Raw`)
- Review in-process files submitted by employees
- **Approve** or **Reject** file versions
- Add improvement suggestions as comments

---

## 🔄 File Lifecycle

Each file in the system moves through a well-defined status workflow:

```
                    ┌─────────────┐
                    │    Raw      │  ← Client uploads initial asset
                    └──────┬──────┘
                           │ Employee uploads processed version
                    ┌──────▼──────┐
                    │ In-Process  │  ← Awaiting client review
                    └──────┬──────┘
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐           ┌──────▼──────┐
       │  Approved   │           │  Rejected   │
       │  (Final)    │           │             │
       └─────────────┘           └──────┬──────┘
                                        │ Employee re-uploads
                                 ┌──────▼──────┐
                                 │ In-Process  │  (new version)
                                 └─────────────┘
```

**Key Rules:**
- A file can only have **one Approved version** at a time
- Once a file is `Approved`, **no further uploads** are allowed
- Employees can only delete **their own** versions that are not yet `Approved`
- Storage quota is **checked before every upload**

---

## 📁 Project Structure

```
DIGITAL ASSET_MANAGEMENT_SYSTEM/
│
├── .env                          # ImageKit API keys (not committed)
├── .gitignore
├── requirements.txt              # Root-level dependencies
│
├── backend/
│   ├── app.py                    # Flask entry point — blueprint registration
│   ├── requirements.txt
│   ├── db/
│   │   ├── connection.py         # MySQL connection factory
│   │   └── schema.sql            # Database schema
│   ├── models/                   # Data-access layer
│   │   ├── user.py
│   │   ├── projects.py
│   │   ├── file.py
│   │   ├── comment.py
│   │   └── permission.py
│   ├── routes/                   # Flask Blueprints (API endpoints)
│   │   ├── user_routes.py
│   │   ├── admin_routes.py
│   │   ├── client_routes.py
│   │   ├── pm_routes.py
│   │   ├── employee_routes.py
│   │   ├── project_routes.py
│   │   ├── file_routes.py
│   │   └── comment_routes.py
│   └── services/
│       └── storage_service.py
│
├── frontend/
│   ├── app.py                    # Streamlit entry point — login + router
│   ├── requirements.txt
│   ├── dashboards/               # Role-specific dashboards
│   │   ├── admin_dashboard.py
│   │   ├── pm_dashboard.py
│   │   ├── employee_dashboard.py
│   │   └── client_dashboard.py
│   ├── components/               # Reusable UI components
│   │   ├── sidebar.py
│   │   ├── navbar.py
│   │   ├── upload_panel.py
│   │   ├── file_grid.py
│   │   ├── file_table.py
│   │   └── folder_grid
│   └── services/                 # API service helpers
│       ├── file_api.py
│       └── project_api.py
│
└── storage/                      # Local temp storage (files pushed to ImageKit)
```

---

## 🗄 Database Schema

The system uses **8 tables** in MySQL:

```sql
User              -- All system users with role and storage quota
Employee          -- Employee-specific data (references User)
Project           -- Projects with client and PM associations
Folder            -- Hierarchical folder structure per project
File              -- File records with version count
File_Version      -- Individual file versions with status and ImageKit URL
Permission        -- Employee access to project folders (granted by PM)
Comment           -- Review comments on files by any role
File_Status_Log   -- Audit table: every status change (populated by DB trigger)
```

### Entity Relationship (Simplified)

```
User ──< Project (as Client)
User ──< Project (as PM)
Project ──< Folder ──< File ──< File_Version
User ──< Permission >── Folder
User ──< Comment >── File
File_Version ──< File_Status_Log
```

> **DB Triggers Used:**
> - On `File_Version` status update → insert into `File_Status_Log`
> - On `File_Version` insert → update `User.storage_used` and `File.total_versions`

---

## 📡 API Reference

### User Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/<role>` | Get all users by role |
| `GET` | `/user/<user_id>` | Get user profile + storage info |
| `GET` | `/employees` | Get all employees |

### Project Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/client/projects` | Create project + folders (transactional) |
| `GET` | `/client/projects?client_id=` | Get client's projects |
| `GET` | `/projects` | Get all projects (admin view) |
| `GET` | `/projects-with-status` | Projects with latest file status |
| `GET` | `/project/full/<project_id>` | Full folder+file tree |
| `GET` | `/project/files/<project_id>` | Files with status flags |
| `GET` | `/pm/projects/<user_id>` | PM's assigned projects |
| `GET` | `/employee/projects/<user_id>` | Employee's assigned projects |

### File Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-to-imagekit` | Upload file to ImageKit CDN |
| `POST` | `/upload-version-to-imagekit` | Upload new version to ImageKit |
| `POST` | `/file/create` | Create simulated file record |
| `POST` | `/simulate/upload/version` | Simulated version (trigger demo) |
| `GET` | `/file/versions/<file_id>` | All versions of a file |
| `GET` | `/file/review/<project_id>` | In-process files awaiting review |
| `GET` | `/file/approved/<project_id>` | All approved files |
| `GET` | `/file/download/<file_id>` | Get approved version CDN URL |
| `GET` | `/file/raw/<file_id>` | Get raw version CDN URL |
| `GET` | `/file/inprocess/<file_id>` | Get in-process version CDN URL |
| `PUT` | `/file/approve/<version_id>` | Approve a file version |
| `PUT` | `/file/reject/<version_id>` | Reject a file version |
| `DELETE` | `/file/version/<version_id>` | Delete a version (own, non-approved) |

### Admin Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/all_users_storage` | All users' storage usage |
| `POST` | `/assign_project` | Assign PM to project |
| `GET` | `/audit/logs` | File status audit log |
| `POST` | `/admin/test_rollback` | Demo: transaction rollback test |

### Employee & PM Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/employee/project_count/<user_id>` | Number of projects assigned |
| `POST` | `/pm/assign_employee` | Assign employee to project (transactional) |
| `GET` | `/project/employees/<project_id>` | Employees on a project |
| `POST` | `/pm/comment` | PM adds review comment |
| `POST` | `/comments` | Add a comment |
| `GET` | `/comments/<file_id>` | Get comments for a file |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MySQL 8.x running locally
- An [ImageKit.io](https://imagekit.io) account
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/digital-asset-management-system.git
cd digital-asset-management-system
```

### 2. Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# OR
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

1. Log in to MySQL and create the database:
   ```sql
   CREATE DATABASE dam_system;
   USE dam_system;
   SOURCE backend/db/schema.sql;
   ```
2. Update credentials in `backend/db/connection.py`:
   ```python
   host="localhost",
   user="your_mysql_user",
   password="your_mysql_password",
   database="dam_system"
   ```

### 5. Configure Environment Variables

Create a `.env` file in the project root:
```env
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_imagekit_id
```

### 6. Start the Backend (Flask API)

```bash
cd backend
python app.py
```
> API running at **http://127.0.0.1:5000**

### 7. Start the Frontend (Streamlit)

Open a **new terminal**:

```bash
cd frontend
streamlit run app.py
```
> UI running at **http://localhost:8501**

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `IMAGEKIT_PRIVATE_KEY` | ✅ Yes | ImageKit private API key for uploads |
| `IMAGEKIT_PUBLIC_KEY` | ✅ Yes | ImageKit public key |
| `IMAGEKIT_URL_ENDPOINT` | ✅ Yes | Your ImageKit URL endpoint |

> ⚠️ **Never commit your `.env` file.** It is included in `.gitignore`.

---

## 🔑 Login

The application uses **role-based login** (no password authentication — select role and user from dropdown):

| Role | Description |
|---|---|
| Admin | System administrator |
| Project Manager | Manages projects and teams |
| Employee | Works on and uploads file assets |
| Client | Project owner who reviews and approves |

---

## 🧱 DBMS Concepts Demonstrated

This project demonstrates the following database concepts:

- ✅ **Normalization** — tables follow 3NF
- ✅ **Foreign Keys & Referential Integrity**
- ✅ **Transactions & Rollback** — atomic multi-step operations
- ✅ **Triggers** — automatic storage tracking and audit logging
- ✅ **Aggregation & Joins** — complex queries across 4–5 tables
- ✅ **Constraints** — unique project names per client, one approval per file
- ✅ **Subqueries** — status flags computed via `EXISTS` subqueries

---






<div align="center">

Built with ❤️ using Flask, Streamlit, MySQL & ImageKit

</div>
