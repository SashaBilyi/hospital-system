from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas, crud, database

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Hospital System API")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
get_db = database.get_db

@app.on_event("startup")
def on_startup():
    db = database.SessionLocal(); crud.seed_data(db); db.close()

# UI
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request): return templates.TemplateResponse("index.html", {"request": request})
@app.get("/doctor-view", response_class=HTMLResponse)
async def read_doctor_view(request: Request): return templates.TemplateResponse("doctor.html", {"request": request})
@app.get("/admin/doctors", response_class=HTMLResponse)
async def read_admin_doctors(request: Request): return templates.TemplateResponse("doctors_manage.html", {"request": request})

# API
@app.get("/departments/", response_model=List[schemas.DepartmentOut])
def read_departments(db: Session = Depends(get_db)): return crud.get_departments(db)
@app.post("/departments/")
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(get_db)): return crud.create_department(db, dept)

@app.get("/patients/", response_model=List[schemas.PatientOut])
def read_patients(search: Optional[str] = None, db: Session = Depends(get_db)): return crud.get_patients(db, search)
@app.post("/patients/", response_model=schemas.PatientOut)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(first_name=patient.first_name, last_name=patient.last_name, date_of_birth=patient.date_of_birth, phone_number=patient.phone_number)
    db.add(db_patient); db.commit(); db.refresh(db_patient); return db_patient
@app.put("/patients/{patient_id}", response_model=schemas.PatientOut)
def update_patient_info(patient_id: int, data: schemas.PatientUpdate, db: Session = Depends(get_db)): return crud.update_patient(db, patient_id, data)
@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)): return crud.soft_delete_patient(db, patient_id)

@app.get("/doctors/")
def read_doctors(specialization: str = None, db: Session = Depends(get_db)): return crud.get_doctors(db, specialization)
@app.post("/doctors/", response_model=schemas.DoctorOut)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)): return crud.create_doctor(db, doctor)
@app.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, data: schemas.DoctorUpdate, db: Session = Depends(get_db)): return crud.update_doctor(db, doctor_id, data)
@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)): return crud.delete_doctor(db, doctor_id)
@app.get("/doctors/{doctor_id}/schedule")
def get_doctor_schedule(doctor_id: int, db: Session = Depends(get_db)): return crud.get_doctor_schedule_settings(db, doctor_id)
@app.put("/doctors/{doctor_id}/schedule")
def update_schedule(doctor_id: int, data: schemas.ScheduleUpdateList, db: Session = Depends(get_db)): return crud.update_doctor_schedule(db, doctor_id, data)
@app.get("/doctors/{doctor_id}/slots", response_model=List[schemas.TimeSlot])
def get_slots(doctor_id: int, date: str, db: Session = Depends(get_db)): return crud.get_slots_for_doctor(db, doctor_id, date)

@app.post("/medications/")
def create_medication(med: schemas.MedicationCreate, db: Session = Depends(get_db)): return crud.create_medication(db, med)
@app.get("/medications/")
def read_medications(db: Session = Depends(get_db)): return crud.get_medications(db)

@app.post("/appointments/", response_model=schemas.AppointmentOut)
def book_appointment(appt: schemas.AppointmentCreate, db: Session = Depends(get_db)): return crud.create_appointment(db, appt)
@app.get("/doctors/{doctor_id}/appointments", response_model=List[schemas.AppointmentOut])
def get_doc_appointments(doctor_id: int, db: Session = Depends(get_db)): return crud.get_doctor_appointments(db, doctor_id)
@app.post("/appointments/{appt_id}/complete")
def complete_visit(appt_id: int, data: schemas.DiagnosisCreate, db: Session = Depends(get_db)): return crud.complete_appointment(db, appt_id, data)
@app.put("/appointments/{appt_id}", response_model=schemas.AppointmentOut)
def reschedule_appointment(appt_id: int, data: schemas.AppointmentUpdate, db: Session = Depends(get_db)): return crud.update_appointment(db, appt_id, data)
@app.post("/appointments/{appt_id}/cancel")
def cancel_appointment(appt_id: int, db: Session = Depends(get_db)): return crud.cancel_appointment(db, appt_id)

@app.get("/patients/{patient_id}/history", response_model=List[schemas.MedicalRecordOut])
def get_history(patient_id: int, db: Session = Depends(get_db)): return crud.get_patient_history(db, patient_id)
@app.get("/analytics/doctors", response_model=List[schemas.DoctorStats])
def get_analytics(db: Session = Depends(get_db)):
    stats = crud.get_top_doctors(db)
    return [schemas.DoctorStats(last_name=row.last_name, specialization=row.specialization or "General", total_visits=row.total_visits, total_revenue=row.total_revenue or 0.0) for row in stats]