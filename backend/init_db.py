"""
Database initialization script
Creates all tables and optionally seeds initial data
"""
import sys
from database import init_db, drop_db, SessionLocal
from models.user import User, UserRole
from models.metrics import ModelMetrics
from utils.security import get_password_hash
from datetime import datetime


def create_admin_user(db):
    """Create default admin user"""
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == "admin@finsentry.com").first()
    
    if existing_admin:
        print("ℹ️  Admin user already exists")
        return
    
    # Create admin user
    admin = User(
        email="admin@finsentry.com",
        username="admin",
        full_name="System Administrator",
        hashed_password=get_password_hash("Admin@123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db.add(admin)
    db.commit()
    
    print("✅ Admin user created:")
    print("   Email: admin@finsentry.com")
    print("   Password: Admin@123")
    print("   ⚠️  Please change the password after first login!")


def create_demo_users(db):
    """Create demo users for testing"""
    demo_users = [
        {
            "email": "manager@finsentry.com",
            "username": "manager",
            "full_name": "Test Manager",
            "role": UserRole.MANAGER,
            "password": "Manager@123"
        },
        {
            "email": "user@finsentry.com",
            "username": "testuser",
            "full_name": "Test User",
            "role": UserRole.USER,
            "password": "User@123"
        }
    ]
    
    for user_data in demo_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            continue
        
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            full_name=user_data["full_name"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        print(f"✅ Created demo user: {user_data['email']}")
    
    db.commit()


def create_initial_metrics(db):
    """Create initial model metrics"""
    existing = db.query(ModelMetrics).first()
    if existing:
        print("ℹ️  Model metrics already exist")
        return
    
    metrics = ModelMetrics(
        model_version="v1.0.0",
        model_type="extraction",
        accuracy=0.92,
        precision=0.89,
        recall=0.91,
        f1_score=0.90,
        training_samples=5000,
        validation_samples=1000,
        test_samples=500,
        feedback_queue_length=0,
        retrain_count=0,
        avg_latency=1250.0,
        p50_latency=950.0,
        p95_latency=2100.0,
        p99_latency=3500.0
    )
    
    db.add(metrics)
    db.commit()
    
    print("✅ Initial model metrics created")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("FinSentry Database Initialization")
    print("=" * 60)
    
    # Check for --reset flag
    reset = "--reset" in sys.argv
    seed = "--seed" in sys.argv or "--with-demo-data" in sys.argv
    
    if reset:
        print("\n⚠️  WARNING: This will DELETE ALL DATA!")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() != "yes":
            print("❌ Operation cancelled")
            return
        
        print("\n🗑️  Dropping all tables...")
        drop_db()
    
    # Initialize database (create tables)
    print("\n🔨 Creating database tables...")
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Always create admin user
        print("\n👤 Creating admin user...")
        create_admin_user(db)
        
        # Optionally seed demo data
        if seed:
            print("\n🌱 Seeding demo data...")
            create_demo_users(db)
            create_initial_metrics(db)
        
        print("\n" + "=" * 60)
        print("✅ Database initialization completed successfully!")
        print("=" * 60)
        
        print("\n📝 Next steps:")
        print("   1. Copy .env.example to .env and configure settings")
        print("   2. Run: uvicorn main:app --reload")
        print("   3. Access API docs at: http://localhost:8000/docs")
        print("   4. Login with admin credentials")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
