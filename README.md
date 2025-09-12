# Dashboard Platform

This project is a **full-stack dashboard application** for uploading, storing, and comparing data.
It integrates with **n8n workflows**, a **FastAPI backend**, and a **React + Tailwind frontend**.

---

## 🚀 Features

* Upload data to the backend via n8n workflows
* Store data and comparisons in a MySQL database
* View comparisons in a React dashboard (scrollable tables)
* Download results as PDFs
* Rules section for displaying long platform guidelines
* Embedded Chat AI assistant for support

---

## 🚀 Tech Stack

### Frontend

* React + TailwindCSS
* shadcn/ui components

### Backend

* Python (FastAPI)
* MySQL (via Docker)
* REST API endpoints

### Workflow

* n8n for automation (data upload → backend → database)

---

## 📂 Project Structure

```
/dashboard-platform
│── /frontend        # React code for dashboard UI
│── /backend         # FastAPI backend
│── README.md        # Project documentation
```

---

## ⚡ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/dashboard-platform.git
cd dashboard-platform
```

### 2. Database (MySQL via Docker)

```bash
docker run --name mysql-db -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=dashboard_db -p 3306:3306 -d mysql:8
```

### 3. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend (React + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

---

## 📝 Usage

* Upload your data via n8n workflow or API endpoint
* View the comparison table in the dashboard
* Scroll to see full comparisons, rules, and chat AI
* Apply changes and save updates back to the backend
* PDF view available for uploaded documents

---

## 💪 Contribution

Contributions are welcome!
Please fork this repo, create a branch, and submit a pull request.

---

## 📜 License

This project is licensed under the MIT License.
