# Лабораторная работа №16 — Django. Вариант 15 «Медицинская клиника»

Модели: `Department`, `Doctor`, `Patient`, `Appointment` (основная), `Diagnosis`.
Связи: `Department 1:N Doctor`, `Doctor 1:N Appointment`, `Patient 1:N Appointment`,
`Appointment N:M Diagnosis`.

## Запуск
```
pip install -r requirements.txt
python manage.py migrate
python manage.py seed          # 30 приёмов, 8 пациентов, 5 врачей; пользователи admin/admin12345 и user/user12345
python manage.py runserver     # http://127.0.0.1:8000/   Admin: http://127.0.0.1:8000/admin/
python manage.py test clinic   # 17 тестов
python manage.py nplus1        # демонстрация N+1 и select_related/prefetch_related
```
PostgreSQL: задать `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (без них используется SQLite).
Секреты: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.

## Страницы
| URL | Назначение | Доступ |
|---|---|---|
| `/` | главная: счётчики объектов, текущий пользователь | все |
| `/appointments/?q=&status=&department=&hide_cancelled=1&sort=&page=` | список: поиск, фильтры, сортировка, пагинация по 10 | вошедшие |
| `/appointments/<id>/` | детальная страница + история посещений пациента (CBV `DetailView`) | вошедшие |
| `/appointments/create/` | создание (FBV + ModelForm) | администратор |
| `/appointments/<id>/edit/` | редактирование (CBV `UpdateView`) | администратор |
| `/appointments/<id>/delete/` | удаление с подтверждением (CBV `DeleteView`) | администратор |
| `/doctors/<id>/` | врач и его записи | вошедшие |
| `/statistics/` | статистика (aggregate, annotate, exists) | вошедшие |

ORM: `all, filter, exclude, get, order_by, count, exists, aggregate, annotate, select_related, prefetch_related`.
Безопасность: CSRF-токены во всех формах, хеширование паролей, права `add/change/delete_appointment`,
экранирование шаблонов.

| Возможность | Django | Flask | FastAPI |
|---|---|---|---|
| ORM | встроенная | нет (SQLAlchemy) | нет (SQLAlchemy) |
| Шаблоны | встроены | Jinja2 | не основной сценарий |
| Admin | встроен | нет | нет |
| Формы | встроены | расширения | Pydantic |
| REST API | через DRF | удобно | основной сценарий |
| OpenAPI | через DRF | расширения | встроено |
| Аутентификация | встроенная | расширения | реализуется отдельно |
