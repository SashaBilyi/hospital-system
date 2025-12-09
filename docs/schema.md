# Схема бази даних

База даних спроєктована в 3НФ і складається з 9 таблиць.

## ER Діаграма
*(Вставте сюди картинку вашої діаграми)*

## Опис таблиць

### 1. `departments`
Довідник відділень лікарні.
- `id`: PK
- `name`: Унікальна назва (напр. "Хірургія")
- `location`: Місцезнаходження

### 2. `doctors`
Інформація про лікарів.
- `id`: PK
- `department_id`: FK -> departments
- `availability_status`: Статус (Available, Vacation, Fired)
- Індекси: `specialization` (для швидкого пошуку)

### 3. `patients`
Клієнти клініки.
- `id`: PK
- `phone_number`: Унікальний, Індекс
- `is_active`: Для Soft Delete (логічного видалення)

### 4. `schedules`
Графік роботи лікарів.
- Дозволяє задавати робочі години для кожного дня тижня окремо.

### 5. `appointments`
Центральна таблиця зв'язку (М:М через сутність).
- `patient_id`: FK
- `doctor_id`: FK
- `status`: scheduled, completed, cancelled
- `symptoms`: Скарги пацієнта

### 6. `medical_records`
Результат завершеного прийому.
- `appointment_id`: FK (Unique) - один запис на один прийом.
- `diagnosis`: Діагноз.

### 7. `prescriptions`
Призначені ліки.
- Зв'язує `medical_records` та `medications`.

### 8. `medications`
Довідник ліків.

### 9. `lab_tests`
Призначені аналізи.