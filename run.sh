#!/bin/bash

set -e

echo "=================================="
echo "  AutoThreatMap - Security Scanner"
echo "=================================="
echo ""

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker Desktop."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo "❌ Docker is not running. Please start Docker Desktop."
        exit 1
    fi

    echo "✓ Docker is running"
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ docker-compose not found. Please install docker-compose."
        exit 1
    fi
    echo "✓ docker-compose is available"
}

start_services() {
    echo ""
    echo "Starting services..."
    echo ""

    docker-compose up -d

    echo ""
    echo "Waiting for services to be ready..."
    sleep 5

    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✓ Backend is ready"
            break
        fi
        echo "  Waiting for backend... ($i/30)"
        sleep 2
    done

    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
}

show_info() {
    echo ""
    echo "=================================="
    echo "  Services are running!"
    echo "=================================="
    echo ""
    echo "Frontend:    http://localhost:5173"
    echo "Backend API: http://localhost:8000"
    echo "API Docs:    http://localhost:8000/docs"
    echo "Health:      http://localhost:8000/health"
    echo ""
    echo "To view logs:    docker-compose logs -f"
    echo "To stop:         docker-compose down"
    echo "To rebuild:      docker-compose up -d --build"
    echo ""
    echo "Demo apps:"
    echo "  - Python Flask:    /demo-apps/python-flask"
    echo "  - Node.js Express: /demo-apps/node-express"
    echo ""
    echo "=================================="
    echo ""
}

case "${1:-start}" in
    start)
        check_docker
        check_docker_compose
        start_services
        show_info
        ;;

    stop)
        echo "Stopping services..."
        docker-compose down
        echo "✓ Services stopped"
        ;;

    restart)
        echo "Restarting services..."
        docker-compose restart
        echo "✓ Services restarted"
        ;;

    rebuild)
        echo "Rebuilding and restarting services..."
        docker-compose down
        docker-compose up -d --build
        echo "✓ Services rebuilt and started"
        ;;

    logs)
        docker-compose logs -f
        ;;

    status)
        docker-compose ps
        ;;

    clean)
        echo "⚠️  This will remove all data. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            docker-compose down -v
            echo "✓ All data cleaned"
        else
            echo "Cancelled"
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|rebuild|logs|status|clean}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  rebuild  - Rebuild and restart services"
        echo "  logs     - Show service logs"
        echo "  status   - Show service status"
        echo "  clean    - Remove all data (destructive)"
        exit 1
        ;;
esac
