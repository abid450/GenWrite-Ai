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

## 📦 Installation

### Prerequisites

```bash
Python 3.10+
Redis Server
Git
PostgreSQL (optional)

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
            }
        ],
        "created_at": "2026-06-07T10:35:00Z",
        "completed_at": "2026-06-07T10:35:12Z"
    },
    "message": "Batch progress retrieved"
}

