from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
import pytest
from datetime import datetime, timedelta


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_patient():
    response = client.post(
        "/patients/",
        json={
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "2000-01-01",
            "phone_number": "+380000000000"
        },
    )
    
    assert response.status_code == 200, f"Error creating patient: {response.text}"
    data = response.json()
    assert data["first_name"] == "Test"
    assert "id" in data

def test_workflow_create_appointment():
    
    res_dept = client.post("/departments/", json={"name": "TestDept", "location": "A1"})
    assert res_dept.status_code == 200, f"Error creating dept: {res_dept.text}"
    dept_id = res_dept.json()["id"] 

    
    res_doc = client.post("/doctors/", json={
        "first_name": "Doc", 
        "last_name": "House", 
        "specialization": "Test", 
        "department_id": dept_id, 
        "price_per_visit": 500,
        "schedule_start": "09:00",
        "schedule_end": "17:00"
    })
    assert res_doc.status_code == 200, f"Error creating doctor: {res_doc.text}"
    doc_id = res_doc.json()["id"]

    
    res_pat = client.post("/patients/", json={
        "first_name": "Pat", 
        "last_name": "Rick", 
        "date_of_birth": "1990-01-01", 
        "phone_number": "+380111111111"
    })
    assert res_pat.status_code == 200, f"Error creating patient: {res_pat.text}"
    pat_id = res_pat.json()["id"]

    
    tomorrow = datetime.now() + timedelta(days=1)
   
    if tomorrow.weekday() >= 5: 
        tomorrow += timedelta(days=2)
    

    future_date = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()

    appt_res = client.post("/appointments/", json={
        "patient_id": pat_id,
        "doctor_id": doc_id,
        "date_time": future_date,
        "symptoms": "Test symptoms"
    })
    
    assert appt_res.status_code == 200, f"Error creating appt: {appt_res.text}"
    data = appt_res.json()
    assert data["status"] == "scheduled"
    assert data["patient"]["id"] == pat_id