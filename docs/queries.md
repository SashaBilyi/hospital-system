# Аналітичні SQL запити

## Топ лікарів за доходом

**Бізнес-питання:** Які лікарі принесли найбільший дохід клініці за весь час?

Цей запит використовується на сторінці "Кабінет лікаря" у блоці "Аналітика".

### SQL Реалізація (SQLAlchemy)

```python
db.query(
    models.Doctor.last_name,
    models.Doctor.specialization,
    func.count(models.Appointment.id).label("total_visits"),
    func.sum(models.Doctor.price_per_visit).label("total_revenue")
).join(models.Appointment)
 .filter(models.Appointment.status == 'completed')
 .group_by(models.Doctor.id)
 .order_by(func.sum(models.Doctor.price_per_visit).desc())
 .all()