#!/bin/bash
# Quick start script for CyberThreat_Ops

echo "🚀 Starting CyberThreat_Ops System..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
echo "  - InfluxDB: http://localhost:8086"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - RabbitMQ: http://localhost:15672 (guest/guest)"
echo "  - API: http://localhost:8000"

echo ""
echo "✅ System is starting up!"
echo ""
echo "📊 Access points:"
echo "  - Dashboard: src/dashboard/index.html (open in browser)"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - System Status: http://localhost:8000/system/status"
echo ""
echo "🎯 Next steps:"
echo "  1. Open src/dashboard/index.html in your browser"
echo "  2. Click 'Train All Models' to train detection algorithms"
echo "  3. Select an attack type and click 'Simulate Attack'"
echo "  4. Watch the system detect and respond to threats!"
echo ""
echo "📖 Run 'python demo.py' for a comprehensive demonstration"
echo ""
