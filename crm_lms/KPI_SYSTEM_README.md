# 📊 Система KPI для менторов

## 📋 Обзор

Система KPI позволяет оценивать эффективность менторов на основе трёх ключевых метрик:
- **Посещаемость** (35%) - процент посещений студентов уроков
- **Оценки** (35%) - средний балл студентов по заданиям
- **Отзывы** (30%) - средняя оценка отзывов студентов

## 🚀 Быстрый старт

### 1. Применение миграций

```bash
python manage.py makemigrations mentors
python manage.py migrate
```

### 2. Регистрация template tags

Добавьте в `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'apps.mentors',
]
```

### 3. Первоначальный расчёт KPI

```python
from apps.mentors.kpi_utils import update_mentor_kpi
from apps.accounts.models import CustomUser

# Обновить KPI для всех менторов
for mentor in CustomUser.objects.filter(role='mentor'):
    update_mentor_kpi(mentor.id)
```

## 📈 API Endpoints

### Получить KPI ментора
```
GET /mentors/api/{mentor_id}/kpi/
```

**Ответ:**
```json
{
    "attendance": 85.0,
    "grades": 78.5,
    "reviews": 92.0,
    "kpi": 84.3,
    "status": "Хорошо",
    "status_code": "good",
    "mentor_name": "Иван Иванов",
    "mentor_email": "ivan@example.com"
}
```

### Обновить KPI ментора
```
POST /mentors/api/{mentor_id}/kpi/update/
```

### Получить KPI всех менторов
```
GET /mentors/api/kpi/
```

### Получить свой KPI (для менторов)
```
GET /mentors/api/my-kpi/
```

## 🎨 Интеграция в шаблоны

### Template Tags

Загрузите template tags:
```html
{% load mentors_tags %}
```

### KPI карточка
```html
{% kpi_card mentor_user show_refresh_button=True %}
```

### Статус KPI в виде бейджа
```html
{{ mentor.kpi_status|kpi_status_badge }}
```

### Цвет KPI
```html
<span style="color: {{ mentor.kpi|kpi_color }}">
    {{ mentor.kpi|default:"0.0" }}
</span>
```

### Получение KPI данных
```html
{% get_mentor_kpi mentor_user as kpi_data %}
KPI: {{ kpi_data.kpi }}
Статус: {{ kpi_data.status }}
```

## 📊 Статусы KPI

| KPI | Статус | Цвет |
|-----|--------|------|
| ≥85 | Рекомендуется | 🟢 Зеленый |
| ≥70 | Хорошо | 🔵 Синий |
| ≥55 | С осторожностью | 🟡 Жёлтый |
| <55 | Не рекомендуется | 🔴 Красный |

## ⚡ Автоматическое обновление

KPI автоматически обновляется при изменении:
- Записей посещаемости (`AttendanceRecord`)
- Оценок студентов (`AssignmentGrade`)
- Отзывов (`LessonFeedback`)

## 🛠 Админка

### Новые поля в модели MentorProfile:
- `kpi` - текущий KPI (FloatField)
- `kpi_status` - статус KPI (CharField)
- `kpi_updated_at` - время последнего обновления

### Действия в админке:
- **Обновить KPI для выбранных** - массовое обновление KPI
- Цветовая индикация статусов
- Фильтрация по KPI статусу

## 📝 Примеры использования

### View с KPI
```python
from apps.mentors.models import MentorProfile
from apps.mentors.kpi_utils import calculate_mentor_kpi

def mentor_detail_with_kpi(request, pk):
    mentor = get_object_or_404(MentorProfile, pk=pk)
    kpi_data = calculate_mentor_kpi(mentor.user.id)
    
    context = {
        'profile': mentor,
        'kpi_data': kpi_data,
    }
    return render(request, 'admin/mentors/detail_with_kpi.html', context)
```

### Cron задача для ежедневного обновления
```python
from django.core.management.base import BaseCommand
from apps.mentors.kpi_utils import update_mentor_kpi
from apps.accounts.models import CustomUser

class Command(BaseCommand):
    def handle(self, *args, **options):
        mentors = CustomUser.objects.filter(role='mentor')
        updated = 0
        
        for mentor in mentors:
            if update_mentor_kpi(mentor.id):
                updated += 1
        
        self.stdout.write(f'KPI обновлён для {updated} менторов')
```

## 🧮 Формула расчёта

```
KPI = attendance * 0.35 + grades * 0.35 + reviews * 0.30
```

### Метрики:

1. **Посещаемость (0-100%)**
   ```
   attendance = (присутствовали / всего возможных) * 100
   ```

2. **Оценки (0-100%)**
   ```
   grades = средний балл всех оценок
   ```

3. **Отзывы (0-100%)**
   ```
   reviews = (средняя оценка отзывов / 5) * 100
   ```

## 🚨 Важные замечания

- Учитываются только **активные** курсы (`status='active'`)
- Пустые данные игнорируются (если нет отзывов, не ломают расчёт)
- Результат округляется до 1 знака после запятой
- Сигналы обновляют KPI автоматически при изменении данных

## 🔄 Обновление системы

Для обновления KPI всех менторов:
```python
from apps.mentors.kpi_utils import update_mentor_kpi
from apps.accounts.models import CustomUser

for mentor in CustomUser.objects.filter(role='mentor'):
    update_mentor_kpi(mentor.id)
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи на наличие ошибок в сигналах
2. Убедитесь, что курсы ментора имеют статус `active`
3. Проверьте наличие данных по посещаемости, оценкам и отзывам
4. Используйте API endpoint для отладки расчётов

---

**Система готова к использованию! 🎉**
