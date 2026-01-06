**🚀 Assistline Backend**

Django REST API backend powering Assistline with authentication, Firebase, PayPal, real-time chat, and geolocation.

🛠️ Tech Stack

Backend: Django & DRF

Database: Firebase Realtime DB & Firestore

Auth: JWT

Payments: PayPal API

Realtime: WebSockets

Extras: Geolocation APIs, Celery, CORS

✨ Core Features

🔑 Auth: JWT, role-based access, secure passwords

📦 REST API: Clean endpoints, validation, error handling

⚡ Realtime: Firebase sync, in-app chat, notifications

💰 Payments: PayPal integration & transaction tracking

📍 Location: Nearby search & distance calculation

🔒 Security: Input validation, secure headers, env config

⚡ Quick Setup
git clone https://github.com/jungleboy36/Assistline_backend.git
cd Assistline_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Add credentials
python manage.py migrate
python manage.py runserver

📡 API Examples

Auth: /api/auth/login, /register, /refresh

Assistants: /api/assistants/ (list, create, update)

Payments: /api/payments/initiate, /verify

Chat: /api/messages/, /conversations/

Locations: /api/locations/nearby, /calculate-distance

👤 Author

GitHub: @jungleboy36
