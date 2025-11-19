# 🍳 Recipe API - Django REST Framework

A comprehensive, production-ready Django REST Framework (DRF) API for recipe management with social features, advanced search, GDPR compliance, and complete test coverage.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green?style=flat-square)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-blue?style=flat-square)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/Coverage-95%25+-brightgreen?style=flat-square)]()

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Authentication & Authorization](#-authentication--authorization)
- [Testing](#-testing)
- [Database](#-database)
- [Docker Deployment](#-docker-deployment)
- [Production Deployment](#-production-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The **Recipe API** is a complete REST API for sharing, discovering, and rating recipes. It features:

- 🔐 **Secure Authentication** with JWT tokens
- 👥 **Social Features** (follow users, like recipes, comment, rate)
- 🔍 **Advanced Search** with filtering and recommendations
- 📸 **Media Support** (images, videos, step-by-step photos)
- 📝 **Recipe Versioning** with edit history
- 💾 **GDPR Compliant** (data export, account deletion)
- 🧪 **95%+ Test Coverage** across all modules
- 📚 **Interactive API Documentation** (Swagger/ReDoc)

Perfect for building a recipe sharing platform, meal planning app, or food blog platform.

---

## ✨ Features

### 👤 User Management
- ✅ User registration with email validation
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ User profiles with bio, profile pictures, social links
- ✅ Follow/unfollow system with follower counts
- ✅ Private messaging between users
- ✅ User activity tracking
- ✅ GDPR compliance: data export & account deletion

### 🍽️ Recipe Management
- ✅ Full CRUD operations (create, read, update, delete)
- ✅ Multiple visibility states: draft, private, pending, public
- ✅ Recipe versioning with complete edit history
- ✅ Ingredient management with auto-scaling
- ✅ Multiple images per recipe with captions
- ✅ Video support and tutorial links
- ✅ Nutrition information tracking
- ✅ Equipment and step-by-step instructions
- ✅ Cooking time, prep time, serving size

### 🏷️ Social & Interaction
- ✅ Comments with spam detection
- ✅ 1-5 star rating system with auto-average calculation
- ✅ Favorite/bookmark recipes
- ✅ Activity feeds from followed users
- ✅ Real-time notifications
- ✅ Recipe collections and meal planning

### 🔍 Search & Discovery
- ✅ Advanced recipe search by title, ingredients, tags
- ✅ Filter by difficulty, cook time, nutrition
- ✅ Trending recipes by rating & views
- ✅ Personalized recommendations
- ✅ Most liked/commented recipes
- ✅ Dietary restriction filtering

### 🔐 Security & Compliance
- ✅ HTTPS support (mkcert locally, Let's Encrypt production)
- ✅ SQL injection prevention via Django ORM
- ✅ Input validation with serializers
- ✅ Rate limiting (100/day authenticated, 20/day anonymous)
- ✅ CORS configuration
- ✅ GDPR data export and deletion endpoints
- ✅ Secure password hashing with PBKDF2

### 📊 Admin & Moderation
- ✅ Django admin interface
- ✅ Content moderation tools
- ✅ Spam flagging system
- ✅ User management
- ✅ Analytics and statistics

### 📚 Documentation
- ✅ OpenAPI 3.0 schema
- ✅ Interactive Swagger UI
- ✅ ReDoc documentation
- ✅ Management commands with help text

---

## 🛠️ Tech Stack

### Core Backend
| Component | Package | Version |
|-----------|---------|---------|
| Web Framework | Django | 4.2.7 |
| REST API | Django REST Framework | 3.14.0 |
| Authentication | djangorestframework-simplejwt | 5.3.2 |
| Database | PostgreSQL / SQLite | Latest |
| Caching | Redis / Memcached | 6.0+ |

### Database & Storage
| Component | Package | Purpose |
|-----------|---------|---------|
| ORM | Django ORM | Database abstraction |
| PostgreSQL Driver | psycopg2-binary | Database connection |
| File Storage | django-storages | Cloud storage support |
| AWS SDK | boto3 | S3 integration |
| Image Processing | Pillow | Image handling |

### API Documentation
| Component | Package |
|-----------|---------|
| OpenAPI Schema | drf-spectacular |
| Alternative Docs | drf-yasg |
| Swagger UI | Built-in (drf-spectacular) |
| ReDoc | Built-in (drf-spectacular) |

### Testing & Quality
| Component | Package | Purpose |
|-----------|---------|---------|
| Test Framework | pytest | Testing |
| Django Integration | pytest-django | Django-specific tests |
| Test Data | factory-boy | Model factories |
| Fake Data | faker | Realistic test data |
| Coverage | coverage | Code coverage reports |
| Code Formatting | black | Code style |
| Linting | flake8, pylint | Code quality |
| Import Sorting | isort | Import organization |

### Deployment
| Component | Package | Purpose |
|-----------|---------|---------|
| WSGI Server | Gunicorn | Production server |
| ASGI Server | Uvicorn | Async support |
| Containerization | Docker | Container images |
| Monitoring | Sentry | Error tracking |

---

## 📁 Project Structure
