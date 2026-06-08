# 🚀 GenWrite AI

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![DRF](https://img.shields.io/badge/DRF-3.14-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-orange)
![Celery](https://img.shields.io/badge/Celery-5.3-brightgreen)
![Redis](https://img.shields.io/badge/Redis-7.0-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

### 🤖 AI-Powered Content Generation Platform

**Write Smarter, Not Harder**

[Features](#✨-features) • [Installation](#📦-installation) • [API Docs](#📚-api-documentation) • [Tech Stack](#🛠️-tech-stack)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Content Generation** | Generate blogs, articles, cover letters with OpenAI |
| ⚡ **Bulk Generation** | Create 100+ contents simultaneously |
| 📊 **Task Management** | Track, cancel, retry failed tasks |
| 👥 **User Authentication** | JWT based secure authentication |
| 📈 **Dashboard Analytics** | Real-time usage statistics |
| 🔄 **Batch Processing** | Process multiple tasks in parallel with Celery |
| 💾 **Caching** | Redis caching for faster responses |
| 📧 **Email Notifications** | Automated email alerts |

---

## 🛠️ Tech Stack

### Backend
| Technology | Icon | Description |
|------------|------|-------------|
| **Django** | 🐍 | High-level Python web framework |
| **Django REST Framework** | 📡 | Powerful API development toolkit |
| **Celery** | 🍎 | Distributed task queue |
| **Redis** | 🔴 | In-memory data structure store |
| **PostgreSQL** | 🐘 | Advanced open-source database |
| **SQLite** | 📁 | Lightweight database (development) |

### AI & Integration
| Technology | Icon | Description |
|------------|------|-------------|
| **OpenAI GPT-3.5 Turbo** | 🤖 | Advanced language model |
| **JWT** | 🔑 | JSON Web Token authentication |

### Monitoring & Tools
| Technology | Icon | Description |
|------------|------|-------------|
| **Flower** | 🌸 | Celery task monitoring dashboard |
| **CeleryX** | 📊 | Celery task result tracking |
| **Celery Results** | 📈 | Task execution history & results |
| **Sentry** | 🚨 | Error tracking & monitoring |
| **Django Debug Toolbar** | 🛠️ | Development debugging tool |
| **Swagger/ReDoc** | 📚 | API documentation |

---
🚀 About Me

I am Abid Hasan, a passionate Backend Engineer specialized in building scalable, high-performance web application, Software using Django, Celery, Redis, and modern AI technologies. I have successfully designed and deployed GenWrite AI — a fully functional AI-powered content generation platform that serves thousands of users with real-time content creation capabilities.

I developed GenWrite AI — a complete AI-powered content generation platform that demonstrates my ability to build production-ready systems.

Key Features:
🤖 AI Content Generation - Integrated OpenAI GPT-3.5 for blog, article, and cover letter generation

⚡ Bulk Processing - Parallel task processing with Celery (100+ tasks simultaneously)

📊 Task Management - Real-time task tracking, cancellation, and retry mechanisms

🔐 Secure Authentication - JWT-based authentication with refresh tokens

📈 Analytics Dashboard - Usage statistics and performance metrics

📧 Email Notifications - Automated email alerts using Celery tasks




## 📦 Installation

### Prerequisites

```bash
Python 3.10+
Redis Server
Git
PostgreSQL (optional)

📁 .env File

# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Database
DB_NAME=genwrite_db
DB_USER=genwrite_user
DB_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

python manage.py makemigrations
python manage.py migrate


🌸 Celery Terminal
# Terminal 1: Redis Server
redis-server

# Terminal 2: Celery Worker
celery -A ai worker --loglevel=info --pool=solo

# Terminal 3: Celery Beat (for scheduled tasks)
celery -A ai beat --loglevel=info

# Terminal 4: Flower Monitoring (Optional)
celery -A ai flower --port=5555

# Terminal 5: Django Server
python manage.py runserver

# Terminal 5 : Celery Starter
python manage.py runcelery -f "celery -A ai flower --port=5555"


📊 Monitoring & Management
Celery Monitoring Tools
Tool	URL	Description
Flower	http://localhost:5555	Real-time Celery task monitoring
CeleryX Admin	http://localhost:8000/admin/celeryx/	Task results in Django Admin
Django Admin	http://localhost:8000/admin/	Database & Task management

🔌 API Endpoints
Authentication
Method	Endpoint	Description
POST	/api/token/	Login & Get JWT Token
POST	/api/token/refresh/	Refresh Token
POST	/api/v1/auth/register/	User Registration
POST	/api/v1/auth/login/	User Login
Content Generation
Method	Endpoint	Description
GET	/api/v1/content/types/	Get Content Types
POST	/api/v1/content/tasks/generate/	Generate Single Content
POST	/api/v1/content/tasks/bulk-generate/	Bulk Content Generation
GET	/api/v1/content/tasks/{id}/	Get Task Status
POST	/api/v1/content/tasks/{id}/cancel/	Cancel Task
POST	/api/v1/content/tasks/{id}/retry/	Retry Failed Task
GET	/api/v1/content/tasks/dashboard/	Dashboard Stats
GET	/api/v1/content/batches/	List All Batches
GET	/api/v1/content/batches/{id}/progress/	Batch Progress

GET http://localhost:8000/api/v1/content/types/
Authorization: Bearer your_access_token

{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "blog",
            "display_name": "Blog Post",
            "description": "Write engaging blog posts",
            "price_per_token": "0.000002",
            "is_active": true
        },
        {
            "id": 2,
            "name": "article",
            "display_name": "Article",
            "description": "Write professional articles",
            "price_per_token": "0.000002",
            "is_active": true
        },
        {
            "id": 3,
            "name": "cover_letter",
            "display_name": "Cover Letter",
            "description": "Write compelling cover letters",
            "price_per_token": "0.000003",
            "is_active": true
        }
    ],
    "message": "Content types retrieved successfully"
}


POST http://localhost:8000/api/v1/content/tasks/generate/
Authorization: Bearer your_access_token
Content-Type: application/json

{
    "prompt": "Write a blog about Python programming for beginners",
    "content_type_id": 1,
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 1000
    }
}

{
    "success": true,
    "data": {
        "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "request_id": "req_abc123def456",
        "status": "pending",
        "estimated_time": 30
    },
    "message": "Content generation started"
}

GET http://localhost:8000/api/v1/content/tasks/f47ac10b-58cc-4372-a567-0e02b2c3d479/
Authorization: Bearer your_access_token


{
    "success": true,
    "data": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "status": "processing",
        "generated_content": null,
        "processing_time": null,
        "tokens_used": 0,
        "created_at": "2026-06-07T10:30:00Z"
    },
    "message": "Task status retrieved"
}

GET http://localhost:8000/api/v1/content/tasks/f47ac10b-58cc-4372-a567-0e02b2c3d479/
Authorization: Bearer your_access_token

{
    "success": true,
    "data": {
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "request_id": "req_abc123def456",
        "user_email": "test@example.com",
        "content_type_name": "Blog Post",
        "prompt": "Write a blog about Python programming for beginners",
        "generated_content": "# Python Programming for Beginners\n\nPython is a powerful, easy-to-learn programming language...\n\n## Why Learn Python?\n- Simple syntax\n- Versatile applications\n- Huge community support\n\n## Getting Started\n1. Install Python\n2. Choose an IDE\n3. Write your first program: `print('Hello, World!')`\n\n## Conclusion\nPython is the perfect language for beginners!",
        "status": "completed",
        "processing_time": 3.45,
        "tokens_used": 450,
        "cost": "0.000900",
        "created_at": "2026-06-07T10:30:00Z",
        "completed_at": "2026-06-07T10:30:03Z"
    },
    "message": "Task completed successfully"
}

📦 Bulk Generate Content

POST http://localhost:8000/api/v1/content/tasks/bulk-generate/
Authorization: Bearer your_access_token
Content-Type: application/json

{
    "batch_name": "Tech Blog Series",
    "requests": [
        {
            "prompt": "Write a blog about Python",
            "content_type_id": 1
        },
        {
            "prompt": "Write a blog about Django",
            "content_type_id": 1
        },
        {
            "prompt": "Write a blog about Machine Learning",
            "content_type_id": 1
        }
    ]
}


Response (202 Accepted):
{
    "success": true,
    "data": {
        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
        "total_tasks": 3,
        "task_ids": [
            "f47ac10b-58cc-4372-a567-0e02b2c3d481",
            "f47ac10b-58cc-4372-a567-0e02b2c3d482",
            "f47ac10b-58cc-4372-a567-0e02b2c3d483"
        ],
        "status": "pending",
        "estimated_time": 9
    },

📊 Get Batch Status
GET http://localhost:8000/api/v1/content/batches/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer your_access_token

{
    "success": true,
    "data": {
        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Tech Blog Series",
        "status": "processing",
        "total_tasks": 3,
        "completed_tasks": 1,
        "failed_tasks": 0,
        "progress_percentage": 33.33,
        "task_status_distribution": {
            "completed": 1,
            "pending": 2
        },
        "created_at": "2026-06-07T10:35:00Z",
        "completed_at": null
    },
    "message": "Batch status retrieved"
}


📊 Get Batch Progress (Completed)

GET http://localhost:8000/api/v1/content/batches/550e8400-e29b-41d4-a716-446655440000/progress/
Authorization: Bearer your_access_token

Response (200 OK - Completed):

{
    "success": true,
    "data": {
        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Tech Blog Series",
        "status": "completed",
        "total_tasks": 3,
        "completed_tasks": 3,
        "failed_tasks": 0,
        "progress_percentage": 100.0,
        "task_status_distribution": {
            "completed": 3
        },
        "tasks": [
            {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d481",
                "status": "completed",
                "content_type_name": "Blog Post",
                "prompt": "Write a blog about Python",
                "generated_content": "# Python Programming\n\nPython is a versatile language...",
                "processing_time": 3.2,
                "tokens_used": 420
            },
            {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d482",
                "status": "completed",
                "content_type_name": "Blog Post",
                "prompt": "Write a blog about Django",
                "generated_content": "# Django Framework\n\nDjango is a high-level Python web framework...",
                "processing_time": 3.5,
                "tokens_used": 450
            },
            {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d483",
                "status": "completed",
                "content_type_name": "Blog Post",
                "prompt": "Write a blog about Machine Learning",
                "generated_content": "# Machine Learning\n\nMachine Learning is a subset of AI...",
                "processing_time": 3.8,
                "tokens_used": 480
            },

        "created_at": "2026-06-07T10:35:00Z",
        "completed_at": "2026-06-07T10:35:12Z"
    },
    "message": "Batch progress retrieved"
}
],        


❌ Cancel Task

POST http://localhost:8000/api/v1/content/tasks/f47ac10b-58cc-4372-a567-0e02b2c3d479/cancel/
Authorization: Bearer your_access_token

Response (200 OK):

{
    "success": true,
    "message": "Task cancelled successfully",
    "data": {
        "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
}

🔄 Retry Failed Task
POST http://localhost:8000/api/v1/content/tasks/f47ac10b-58cc-4372-a567-0e02b2c3d480/retry/
Authorization: Bearer your_access_token

Response (202 Accepted):

{
    "success": true,
    "data": {
        "new_task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d484",
        "original_task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
        "status": "pending",
        "retry_count": 1
    },
    "message": "Task regeneration started"
}

📈 Dashboard Statistics
GET http://localhost:8000/api/v1/content/tasks/dashboard/
Authorization: Bearer your_access_token

Response (200 OK):

{
    "success": true,
    "data": {
        "summary": {
            "total_tasks": 45,
            "completed_tasks": 38,
            "pending_tasks": 3,
            "processing_tasks": 2,
            "failed_tasks": 2,
            "cancelled_tasks": 0,
            "completion_rate": 84.44,
            "avg_processing_time": 3.45,
            "total_tokens_used": 18750,
            "total_cost": "0.037500"
        },
        "daily_stats": [
            {"day": "2026-06-01", "count": 5},
            {"day": "2026-06-02", "count": 8},
            {"day": "2026-06-03", "count": 12},
            {"day": "2026-06-04", "count": 7},
            {"day": "2026-06-05", "count": 6},
            {"day": "2026-06-06", "count": 4},
            {"day": "2026-06-07", "count": 3}
        ]
    },
    "message": "Dashboard statistics retrieved"
}

📊 Status Summary
GET http://localhost:8000/api/v1/content/tasks/status-summary/
Authorization: Bearer your_access_token

Response (200 OK):

{
    "success": true,
    "data": {
        "pending": 3,
        "processing": 2,
        "completed": 38,
        "failed": 2,
        "cancelled": 0
    },
    "message": "Status summary retrieved"
}

📋 Get All Batches
GET http://localhost:8000/api/v1/content/batches/
Authorization: Bearer your_access_token

Response (200 OK):
{
    "success": true,
    "data": {
        "count": 8,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Tech Blog Series",
                "status": "completed",
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "progress_percentage": 100.0,
                "created_at": "2026-06-07T10:35:00Z",
                "completed_at": "2026-06-07T10:35:12Z"
            },
            {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "name": "Marketing Content",
                "status": "processing",
                "total_tasks": 5,
                "completed_tasks": 2,
                "failed_tasks": 0,
                "progress_percentage": 40.0,
                "created_at": "2026-06-07T11:00:00Z",
                "completed_at": null
            }
        ]
    },
    "message": "Batches retrieved successfully"
}




📐 Detailed System Architecture

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  React   │  │   Vue    │  │ Angular  │  │  Mobile  │  │  cURL/   │      │
│  │   Web    │  │   Web    │  │   Web    │  │   App    │  │ Postman  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │             │             │
│       └─────────────┴─────────────┴─────────────┴─────────────┘             │
│                                    │ HTTPS                                  │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                          LOAD BALANCER LAYER                                │
│                                     ▼                                       │
│                          ┌─────────────────┐                               │
│                          │  Nginx/HAProxy  │                               │
│                          │  Port: 80/443   │                               │
│                          └────────┬────────┘                               │
└───────────────────────────────────┼────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────┐
│                         APPLICATION LAYER                                   │
│                    ┌────────────────┴────────────────┐                     │
│                    ▼                                 ▼                     │
│     ┌─────────────────────────┐     ┌─────────────────────────┐           │
│     │   Django App Server 1   │     │   Django App Server 2   │           │
│     │   (Gunicorn - 4 workers)│     │   (Gunicorn - 4 workers)│           │
│     └───────────┬─────────────┘     └───────────┬─────────────┘           │
│                 │                               │                          │
│                 └───────────────┬───────────────┘                          │
│                                 │                                          │
│     ┌───────────────────────────┴───────────────────────────┐             │
│     │                                                       │             │
│     ▼                       ▼                               ▼             │
│ ┌─────────────┐     ┌─────────────┐               ┌─────────────┐         │
│ │  API Layer  │     │  Admin UI   │               │  Swagger/   │         │
│ │   (DRF)     │     │  (Jazzmin)  │               │   ReDoc     │         │
│ └─────────────┘     └─────────────┘               └─────────────┘         │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────┐
│                         TASK QUEUE LAYER                                    │
│                                 │                                          │
│                    ┌────────────┴────────────┐                            │
│                    ▼                         ▼                            │
│     ┌─────────────────────────┐   ┌─────────────────────────┐             │
│     │   Celery Beat           │   │   Celery Worker Pool    │             │
│     │   (Scheduler)           │◄──│   (High Priority)       │             │
│     │   - Periodic Tasks      │   │   - Content Generation  │             │
│     │   - Daily Reports       │   │   - 10 workers          │             │
│     └───────────┬─────────────┘   └───────────┬─────────────┘             │
│                 │                             │                            │
│                 │              ┌──────────────┴──────────────┐             │
│                 │              ▼                             ▼             │
│                 │   ┌─────────────────────┐   ┌─────────────────────┐      │
│                 │   │  Celery Worker      │   │  Celery Worker      │      │
│                 │   │  (Bulk Queue)       │   │  (Email Queue)      │      │
│                 │   │  - 5 workers        │   │  - 3 workers        │      │
│                 │   └─────────────────────┘   └─────────────────────┘      │
└─────────────────┼─────────────────────────────────────────────────────────┘
                  │
┌─────────────────┼─────────────────────────────────────────────────────────┐
│                          DATABASE & CACHE LAYER                            │
│                 │                                                         │
│    ┌────────────┴────────────┬────────────────────┬───────────────────┐  │
│    ▼                         ▼                    ▼                   ▼  │
│ ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│ │  PostgreSQL  │    │   Redis      │    │   Redis      │    │   Redis    ││
│ │  Primary DB  │    │   Cache      │    │   Session    │    │  Broker    ││
│ │  - Tasks     │    │  - API Cache │    │  - User Auth │    │  - Celery  ││
│ │  - Users     │    │  - Rate Limit│    │  - Sessions  │    │  - Message ││
│ │  - Batches   │    │  - Templates │    │              │    │            ││
│ └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘│
│         │                                                                  │
│         ▼                                                                  │
│ ┌──────────────┐                                                          │
│ │  PostgreSQL  │                                                          │
│ │  Replica DB  │                                                          │
│ │  - Read Only │                                                          │
│ └──────────────┘                                                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                   │
│                 │                                                          │
│    ┌────────────┴────────────┬────────────────────┬────────────────┐      │
│    ▼                         ▼                    ▼                ▼      │
│ ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  ┌─────────────┐  │
│ │  OpenAI API  │    │  Gmail/SMTP  │    │   Stripe     │  │   AWS S3    │  │
│ │  - GPT-3.5   │    │  - Email     │    │  - Payment   │  │  - Media    │  │
│ │  - Embeddings│    │  - Notify    │    │  - Webhook   │  │  - Static   │  │
│ └──────────────┘    └──────────────┘    └──────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────┐
│                         MONITORING LAYER                                    │
│                 │                                                          │
│    ┌────────────┴────────────┬────────────────────┬────────────────┐      │
│    ▼                         ▼                    ▼                ▼      │

│ ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  ┌─────────────┐  │
│ │   Flower     │    │   Sentry     │    │  Prometheus  │  │  Grafana    │  │
│ │  - Celery    │    │  - Errors    │    │  - Metrics   │  │  - Visual   │  │
│ │  - Tasks     │    │  - Logs      │    │  - Alerts    │  │  - Dashboard│  │
│ │  :5555       │    │              │    │              │  │             │  │
│ └──────────────┘    └──────────────┘    └──────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
