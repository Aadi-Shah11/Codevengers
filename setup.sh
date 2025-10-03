#!/bin/bash

# Smart Campus Access Control - Setup Script
# This script sets up the development environment for the hackathon project

echo "🚀 Setting up Smart Campus Access Control System..."

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/database backend/services backend/models backend/routers
mkdir -p mobile/lib/models mobile/lib/screens mobile/lib/services mobile/lib/widgets
mkdir -p mobile/assets/images mobile/assets/icons
mkdir -p web-dashboard/assets

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

# Database setup
echo "🗄️ Setting up MySQL database..."
echo "Testing database connection..."
python database/test_connection.py

echo ""
echo "To initialize the database, run:"
echo "python database/init_db.py"
echo ""
echo "Or manually execute:"
echo "1. mysql -u root -p < database/schema.sql"
echo "2. mysql -u root -p < database/seed_data.sql"
echo "3. mysql -u root -p < database/indexes.sql"
echo "4. mysql -u root -p < database/views.sql"
echo "5. mysql -u root -p < database/procedures.sql"

cd ..

# Flutter setup
echo "📱 Setting up Flutter mobile app..."
cd mobile

# Get Flutter dependencies
flutter pub get

echo "✅ Flutter dependencies installed"

cd ..

# Web dashboard setup
echo "🌐 Web dashboard is ready to use"
echo "Open web-dashboard/index.html in a browser"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the system:"
echo "1. Start MySQL database"
echo "2. Run backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Run Flutter app: cd mobile && flutter run"
echo "4. Open web-dashboard/index.html in browser"
echo ""
echo "📚 Check README.md for detailed instructions"