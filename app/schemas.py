from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List

class DepartmentCreate(BaseModel):
    name: str
    location: str

class DepartmentOut(DepartmentCreate):
    id: int
    class Config: from_attributes = True

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    phone_number: str

class PatientCreate(PatientBase): pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

class DoctorCreate(BaseModel):
    first_name: str
    last_name: str
    specialization: str
    department_id: int
    price_per_visit: float
    schedule_start: Optional[str] = "09:00"
    schedule_end: Optional[str] = "17:00"

class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    specialization: Optional[str] = None
    price_per_visit: Optional[float] = None
    availability_status: Optional[str] = None

class DoctorOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    specialization: str
    price_per_visit: float
    availability_status: str
    class Config: from_attributes = True

class ScheduleItem(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

class ScheduleUpdateList(BaseModel):
    schedules: List[ScheduleItem]

class TimeSlot(BaseModel):
    time: str
    is_free: bool

class MedicationCreate(BaseModel):
    medication_name: str
    manufacturer: str
    description: str

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    date_time: datetime
    symptoms: Optional[str] = None

class AppointmentUpdate(BaseModel):
    date_time: Optional[datetime] = None
    symptoms: Optional[str] = None

class PrescriptionItem(BaseModel):
    medication_name: str
    dosage: str
    instructions: str

class DiagnosisCreate(BaseModel):
    diagnosis: str
    treatment_plan: str
    prescriptions: List[PrescriptionItem]

class PatientOut(PatientBase):
    id: int
    class Config: from_attributes = True

class AppointmentOut(BaseModel):
    id: int
    date_time: datetime
    status: str
    patient: PatientOut
    symptoms: Optional[str]
    class Config: from_attributes = True

class MedicalRecordOut(BaseModel):
    date: datetime
    diagnosis: str
    treatment_plan: str
    doctor_name: str
    class Config: from_attributes = True

class DoctorStats(BaseModel):
    last_name: str
    specialization: str
    total_visits: int
    total_revenue: float