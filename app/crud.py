from sqlalchemy.orm import Session
from sqlalchemy import func, or_, cast, String
from datetime import datetime, timedelta, date, time
import random
from . import models, schemas
from fastapi import HTTPException


def get_kyiv_time():
    return datetime.utcnow() + timedelta(hours=2)


def seed_data(db: Session):
    if db.query(models.Department).first(): return 
    print("--- 🚀 SEEDING ---")
    departments_data = [{"name": "Хірургія", "loc": "A"}, {"name": "Терапія", "loc": "B"}, {"name": "Неврологія", "loc": "C"}, {"name": "Педіатрія", "loc": "D"}, {"name": "Кардіологія", "loc": "E"}]
    depts = []
    for d in departments_data:
        dept = models.Department(name=d["name"], location=d["loc"])
        db.add(dept); depts.append(dept)
    db.commit()
    for d in depts: db.refresh(d)

    names = ["Олександр", "Андрій", "Василь", "Ірина", "Олена", "Марія", "Світлана", "Віктор", "Наталія", "Дмитро"]
    surnames = ["Шевченко", "Коваленко", "Бойко", "Ткаченко", "Кравчук", "Олійник", "Вовк", "Поліщук", "Бондар", "Мельник"]
    doctors = []
    for i in range(15):
        dept = depts[i % 5]
        doc = models.Doctor(
            first_name=random.choice(names), last_name=random.choice(surnames),
            specialization=dept.name[:-2] if len(dept.name)>5 else "Лікар",
            department_id=dept.id, price_per_visit=random.choice([500, 700, 1000]),
            availability_status="Available"
        )
        db.add(doc); doctors.append(doc)
    db.commit()
    
    for doc in doctors:
        db.refresh(doc)
        for day in ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]:
            db.add(models.Schedule(doctor_id=doc.id, day_of_week=day, start_time=time(9,0), end_time=time(17,0)))
    db.commit()

    for m in [("Аспірин", "Bayer", "Жар"), ("Ібупрофен", "Дарниця", "Біль"), ("Вітамін C", "Віт", "Імун")]:
        db.add(models.Medication(medication_name=m[0], manufacturer=m[1], description=m[2]))
    
    pat_names = ["Іван", "Петро", "Максим", "Анна"]
    for i in range(25):
        db.add(models.Patient(first_name=random.choice(pat_names), last_name=random.choice(surnames), date_of_birth=date(1990,1,1), phone_number=f"+380{random.randint(100000000, 999999999)}"))
    db.commit()
    print("--- SEEDING DONE ---")


def create_department(db: Session, dept: schemas.DepartmentCreate):
    db_dept = models.Department(name=dept.name, location=dept.location)
    db.add(db_dept); db.commit(); db.refresh(db_dept); return db_dept

def create_doctor(db: Session, doctor: schemas.DoctorCreate):
    db_doc = models.Doctor(
        first_name=doctor.first_name, last_name=doctor.last_name, specialization=doctor.specialization,
        department_id=doctor.department_id, price_per_visit=doctor.price_per_visit, availability_status="Available"
    )
    db.add(db_doc); db.commit(); db.refresh(db_doc)
    try: start_t = datetime.strptime(doctor.schedule_start, '%H:%M').time(); end_t = datetime.strptime(doctor.schedule_end, '%H:%M').time()
    except: start_t = time(9,0); end_t = time(17,0)
    for day in ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]:
        db.add(models.Schedule(doctor_id=db_doc.id, day_of_week=day, start_time=start_t, end_time=end_t))
    db.commit(); db.refresh(db_doc); return db_doc

def create_medication(db: Session, med: schemas.MedicationCreate):
    db_med = models.Medication(medication_name=med.medication_name, manufacturer=med.manufacturer, description=med.description)
    db.add(db_med); db.commit(); db.refresh(db_med); return db_med

def create_appointment(db: Session, data: schemas.AppointmentCreate):
    try:
        now_kyiv = get_kyiv_time()
        if data.date_time < now_kyiv.replace(tzinfo=None) - timedelta(minutes=5): raise HTTPException(400, "Минулий час")
        
        patient = db.query(models.Patient).filter(models.Patient.id == data.patient_id).first()
        if not patient or not patient.is_active: raise HTTPException(400, "Patient inactive")
        
        doctor = db.query(models.Doctor).filter(models.Doctor.id == data.doctor_id).first()
        if not doctor or doctor.availability_status != "Available": raise HTTPException(404, "Doctor unavailable")
        
        day_str = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"][data.date_time.weekday()]
        sched = db.query(models.Schedule).filter(models.Schedule.doctor_id == data.doctor_id, models.Schedule.day_of_week == day_str).first()
        if not sched: raise HTTPException(400, f"Не працює в {day_str}")
        if data.date_time.time() < sched.start_time or data.date_time.time() >= sched.end_time: raise HTTPException(400, "Поза робочим часом")
        
        if db.query(models.Appointment).filter(models.Appointment.doctor_id==data.doctor_id, models.Appointment.date_time==data.date_time, models.Appointment.status!='cancelled').first():
            raise HTTPException(409, "Час зайнятий")

        new_appt = models.Appointment(patient_id=data.patient_id, doctor_id=data.doctor_id, date_time=data.date_time, symptoms=data.symptoms, status="scheduled")
        db.add(new_appt); db.commit(); db.refresh(new_appt); return new_appt
    except Exception as e: db.rollback(); raise e

def get_slots_for_doctor(db: Session, doctor_id: int, date_str: str):
    try: target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except: return []
    now_kyiv = get_kyiv_time()
    if target_date < now_kyiv.date(): return []
    
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doc or doc.availability_status != "Available": return []
    
    day_name = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"][target_date.weekday()]
    schedule = db.query(models.Schedule).filter(models.Schedule.doctor_id == doctor_id, models.Schedule.day_of_week == day_name).first()
    if not schedule: return []
    
    start_d = datetime.combine(target_date, time.min); end_d = datetime.combine(target_date, time.max)
    appts = db.query(models.Appointment).filter(models.Appointment.doctor_id==doctor_id, models.Appointment.date_time>=start_d, models.Appointment.date_time<=end_d, models.Appointment.status!='cancelled').all()
    busy = {a.date_time.time() for a in appts}
    
    slots = []; curr = schedule.start_time
    while (datetime.combine(date.min, curr) + timedelta(minutes=20)).time() <= schedule.end_time:
        is_free = curr not in busy
        if target_date == now_kyiv.date() and curr < now_kyiv.time(): is_free = False
        slots.append({"time": curr.strftime("%H:%M"), "is_free": is_free})
        curr = (datetime.combine(date.min, curr) + timedelta(minutes=20)).time()
    return slots


def get_medications(db: Session): return db.query(models.Medication).all()
def get_departments(db: Session): return db.query(models.Department).all()
def get_doctors(db: Session, specialization: str = None):
    q = db.query(models.Doctor)
    if specialization: q = q.filter(models.Doctor.specialization == specialization)
    return q.all()

def get_patients(db: Session, search: str = None):
    q = db.query(models.Patient).filter(models.Patient.is_active == True)
    if search:
        s = f"%{search}%"
        q = q.filter(or_(models.Patient.first_name.ilike(s), models.Patient.last_name.ilike(s), models.Patient.phone_number.ilike(s), cast(models.Patient.date_of_birth, String).ilike(s)))
    return q.order_by(models.Patient.id.asc()).all()

def get_doctor_appointments(db: Session, doctor_id: int):
    return db.query(models.Appointment).filter(models.Appointment.doctor_id == doctor_id, models.Appointment.status != 'cancelled').order_by(models.Appointment.date_time.asc()).all()
def get_doctor_schedule_settings(db: Session, doctor_id: int): return db.query(models.Schedule).filter(models.Schedule.doctor_id == doctor_id).all()
def get_patient_history(db: Session, patient_id: int):
    appts = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id, models.Appointment.status == 'completed').all()
    res = []
    for a in appts:
        if a.diagnosis: res.append({"date": a.date_time, "diagnosis": a.diagnosis, "treatment_plan": "Див. рецепт", "doctor_name": f"{a.doctor.first_name} {a.doctor.last_name}"})
    return res


def update_patient(db: Session, patient_id: int, data: schemas.PatientUpdate):
    p = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not p: raise HTTPException(404, "Not found")
    if data.first_name: p.first_name = data.first_name
    if data.last_name: p.last_name = data.last_name
    if data.phone_number: p.phone_number = data.phone_number
    db.commit(); db.refresh(p); return p

def update_doctor(db: Session, doctor_id: int, data: schemas.DoctorUpdate):
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doc: raise HTTPException(404, "Not found")
    if data.first_name: doc.first_name = data.first_name
    if data.last_name: doc.last_name = data.last_name
    if data.specialization: doc.specialization = data.specialization
    if data.price_per_visit: doc.price_per_visit = data.price_per_visit
    if data.availability_status:
        doc.availability_status = data.availability_status
        if data.availability_status == "Available" and not db.query(models.Schedule).filter(models.Schedule.doctor_id == doctor_id).first():
            for day in ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]:
                db.add(models.Schedule(doctor_id=doc.id, day_of_week=day, start_time=time(9,0), end_time=time(17,0)))
    db.commit(); db.refresh(doc); return doc

def update_doctor_schedule(db: Session, doctor_id: int, data: schemas.ScheduleUpdateList):
    for item in data.schedules:
        try: t_s = datetime.strptime(item.start_time, '%H:%M').time(); t_e = datetime.strptime(item.end_time, '%H:%M').time()
        except: continue
        s = db.query(models.Schedule).filter(models.Schedule.doctor_id == doctor_id, models.Schedule.day_of_week == item.day_of_week).first()
        if s: s.start_time=t_s; s.end_time=t_e
        else: db.add(models.Schedule(doctor_id=doctor_id, day_of_week=item.day_of_week, start_time=t_s, end_time=t_e))
    db.commit(); return {"status": "Updated"}

def update_appointment(db: Session, appt_id: int, data: schemas.AppointmentUpdate):
    a = db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()
    if not a: raise HTTPException(404, "Not found")
    if data.symptoms: a.symptoms = data.symptoms
    if data.date_time:
        if data.date_time < get_kyiv_time().replace(tzinfo=None): raise HTTPException(400, "Минулий час")
        if db.query(models.Appointment).filter(models.Appointment.doctor_id==a.doctor_id, models.Appointment.date_time==data.date_time, models.Appointment.status!='cancelled', models.Appointment.id!=appt_id).first():
            raise HTTPException(409, "Зайнято")
        a.date_time = data.date_time
    db.commit(); db.refresh(a); return a

def cancel_appointment(db: Session, appt_id: int):
    a = db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()
    if not a: raise HTTPException(404, "Not found")
    a.status = "cancelled"; a.symptoms = (a.symptoms or "") + " [СКАСОВАНО]"; db.commit(); return {"status": "cancelled"}


def complete_appointment(db: Session, appointment_id: int, data: schemas.DiagnosisCreate):
    try:
        appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
        if not appt: raise HTTPException(404, "Appointment not found")
        
        appt.status = "completed"
        appt.diagnosis = data.diagnosis
        
        existing_record = db.query(models.MedicalRecord).filter(models.MedicalRecord.appointment_id == appt.id).first()
        
        if existing_record:
            med_record = existing_record
            med_record.diagnosis = data.diagnosis 
            med_record_id = med_record.id
        else:
            med_record = models.MedicalRecord(
                patient_id=appt.patient_id, 
                appointment_id=appt.id, 
                diagnosis=data.diagnosis, 
                treatment_plan=data.treatment_plan, 
                allergies="Unknown", 
                chronic_conditions="None", 
                blood_type="UNK"
            )
            db.add(med_record)
            db.flush()
            med_record_id = med_record.id
        
        for item in data.prescriptions:
            med_name = item.medication_name.strip()
            med = db.query(models.Medication).filter(models.Medication.medication_name == med_name).first()
            if not med:
                med = models.Medication(medication_name=med_name, manufacturer="Інше", description="Авто")
                db.add(med); db.flush()
            
            db.add(models.Prescription(
                appointment_id=appt.id, 
                record_id=med_record_id, 
                medication_id=med.medication_id, 
                dosage=item.dosage, 
                instructions=item.instructions
            ))
        db.commit()
        return {"status": "success"}
    except Exception as e: db.rollback(); raise e

def soft_delete_patient(db: Session, patient_id: int):
    p = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not p: raise HTTPException(404, "Not found")
    p.is_active = False
    for a in db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id, models.Appointment.status == "scheduled").all():
        a.status = "cancelled"; a.symptoms = (a.symptoms or "") + " [DELETED]"
    db.commit(); return {"status": "deactivated"}

def delete_doctor(db: Session, doctor_id: int):
    d = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not d: raise HTTPException(404, "Not found")
    d.availability_status = "Fired"
    db.query(models.Schedule).filter(models.Schedule.doctor_id == doctor_id).delete()
    db.commit(); return {"status": "Fired"}

def get_top_doctors(db: Session):
    return db.query(models.Doctor.last_name, models.Doctor.specialization, func.count(models.Appointment.id).label("total_visits"), func.sum(models.Doctor.price_per_visit).label("total_revenue")).join(models.Appointment).filter(models.Appointment.status == 'completed').group_by(models.Doctor.id).order_by(func.sum(models.Doctor.price_per_visit).desc()).all()