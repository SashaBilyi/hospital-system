from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Text, TIMESTAMP, Time, Float
from sqlalchemy.orm import relationship
from .database import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(255))
    doctors = relationship("Doctor", back_populates="department")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    specialization = Column(String(100))
    availability_status = Column(String(50), default="Available")
    price_per_visit = Column(Float, default=500.0)
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")
    schedules = relationship("Schedule", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone_number = Column(String(20), unique=True)
    is_active = Column(Boolean, default=True) 
    appointments = relationship("Appointment", back_populates="patient")
    medical_record = relationship("MedicalRecord", back_populates="patient", uselist=False)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    date_time = Column(TIMESTAMP, nullable=False)
    status = Column(String(20), default="scheduled")
    diagnosis = Column(Text)
    symptoms = Column(Text)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    medical_record = relationship("MedicalRecord", back_populates="appointment", uselist=False)
    prescriptions = relationship("Prescription", back_populates="appointment")
    lab_tests = relationship("LabTest", back_populates="appointment")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    allergies = Column(Text)
    chronic_conditions = Column(Text)
    blood_type = Column(String(5))
    patient = relationship("Patient", back_populates="medical_record")
    appointment = relationship("Appointment", back_populates="medical_record")
    prescriptions = relationship("Prescription", back_populates="medical_record")

class Medication(Base):
    __tablename__ = "medications"
    medication_id = Column(Integer, primary_key=True, index=True)
    medication_name = Column(String(100), nullable=False)
    manufacturer = Column(String(100))
    description = Column(Text)
    prescriptions = relationship("Prescription", back_populates="medication")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    record_id = Column(Integer, ForeignKey("medical_records.id"))
    medication_id = Column(Integer, ForeignKey("medications.medication_id"))
    dosage = Column(String(100))
    instructions = Column(Text)
    appointment = relationship("Appointment", back_populates="prescriptions")
    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
    medication = relationship("Medication", back_populates="prescriptions")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    day_of_week = Column(String(20))
    start_time = Column(Time)
    end_time = Column(Time)
    doctor = relationship("Doctor", back_populates="schedules")

class LabTest(Base):
    __tablename__ = "lab_tests"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    test_name = Column(String(100), nullable=False)
    test_date = Column(Date)
    results = Column(Text)
    appointment = relationship("Appointment", back_populates="lab_tests")