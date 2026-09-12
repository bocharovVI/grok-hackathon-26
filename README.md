# Medical History

Хакатонный MVP: React/Vite → FastAPI → Grok x.ai → PostgreSQL.
Пользователь регистрируется, заполняет анкету, загружает PDF/PNG/JPEG/WEBP и
получает JSON по `outpatient_visit_general.schema.json`. Из документов извлекаются
записанные врачами сведения; новые диагнозы и назначения приложение не генерирует.

## Локальный запуск

Python 3.12, Node 22, PostgreSQL 16. Команды выполняются из корня репозитория.
Копируйте примеры `.env` только при первоначальной настройке, чтобы не затереть свои значения.

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

В `.env` укажите `XAI_API_KEY`; `XAI_MODEL` должен поддерживать изображения и
structured outputs (по умолчанию `grok-4.6`). Ключ используется только backend.
На Windows активация окружения: `.venv\Scripts\activate`.

В другом терминале:

```bash
cd frontend
npm ci
npm run dev
```

Откройте `http://localhost:5173`. Swagger: `http://localhost:8000/api/docs`.
`/docs` зарезервирован для API документов, а не Swagger.
Деморежим включается только явно: `VITE_USE_MOCK=true`; реальные медицинские
данные и пароли в нём не используйте. Отсутствующий URL API больше не включает mock.

## Контракты и хранение

- `POST /auth/signup`, `/auth/login`: `{email, password}` → `{id, email, profileComplete, token}`.
- `POST /auth/logout`: отзывает текущий Bearer-токен. В БД хранится только его хеш; срок жизни — 7 дней.
- Сохранён `POST /auth/register`: обязательны email, password, first_name, last_name;
  возвращает пациента, после него нужен `/auth/login`. Ограничение bcrypt — 72 байта UTF-8.
- `GET /me`, `GET/PUT /me/profile`: контракт анкеты фронтенда.
- `POST /docs`: multipart-поле `file`; ответ 201 только после разбора и фиксации транзакции.
- `GET /docs`, `/docs/{id}`, `/docs/{id}/file`: документы только текущего пациента.
- `GET /overview`: найденные диагнозы, препараты и операции.
- `GET/POST /diagnosis`: сводка диагнозов из документов, либо `null`, если диагнозов нет.

PDF рендерится постранично, включая сканированные PDF. Изображения нормализуются
в JPEG и передаются Grok через `chat/completions` с `response_format=json_schema`.
Используется `prompt_medical_document_parser_v3.md`. Полный ответ проверяется
JSON Schema Draft 2020-12 с проверкой форматов и связей до записи в БД.

Связи из `grok_hackathon.drawio.xml` реализованы в таблицах `patients`, `documents`,
`medical_organizations`, `doctors`, `medications`, `operations`, `diagnoses`.
Дополнительно сохраняются `medical_visits`, `recommendations` и `auth_sessions`.
Пациент одновременно является учётной записью (как в существующем backend);
отдельная таблица пользователей и `user_id` для MVP не требуются. Извлечённые
персональные сведения остаются в JSON и не перезаписывают профиль/учётные данные.

Основные клинические поля находятся в отдельных колонках, расширенные поля
(анамнез, осложнения, дополнительные даты и т. п.) — в `details` соответствующих
строк. Полный JSON хранится в `documents.extracted`. FK `document_id` сохраняет
семантику схемы, а `source_document_id` всегда указывает фактический источник
импорта, в том числе для исторических записей. UUID новых сущностей назначает
backend с согласованным обновлением ссылок; UUID из LLM не обновляют чужие строки.
Весь импорт фиксируется одной транзакцией; ошибки не оставляют частичных записей.

Исходные файлы хранятся в PostgreSQL (`bytea`), а не на эфемерном диске Render.
Название `s3_url` сохранено для совместимости контракта, но содержит защищённый
URL `/docs/{id}/file`, а не ссылку на S3. Просмотр требует Bearer-токен; фронтенд
получает файл через авторизованный запрос и отображает локальный blob URL.

Согласованы противоречия схемы и промпта: разрешены госпитализация и `null` для
неизвестного МКБ-10/врача/организации; отсутствующие ФИО, дата рождения, адрес,
специализация, даты событий и режим приёма необязательны. `password_hash` исключён
из контракта медицинского парсера. Версия 3.0 сохранена, существующие заполненные
объекты совместимы. Препарат без числовой дозировки не создаёт отдельную строку,
как предписывает промпт.

## Render

`render.yaml` описывает static frontend, Python backend и PostgreSQL. Backend
использует план Starter и БД basic-256mb: эти ресурсы платные. Миграции выполняются
командой `alembic upgrade head` перед запуском backend. `staticPublishPath: dist`
указан относительно `rootDir: frontend`.

При создании Blueprint укажите следующие значения (реальные домены смотрите в Render):

| Переменная | Сервис | Значение |
| --- | --- | --- |
| `XAI_API_KEY` | backend | Ключ x.ai |
| `PUBLIC_API_URL` | backend | Публичный HTTPS URL backend, без завершающего `/` |
| `CORS_ORIGINS` | backend | JSON-массив точных origin фронтенда, например `["https://your-frontend.onrender.com"]` |
| `VITE_API_URL` | frontend | Тот же публичный HTTPS URL backend |

`DATABASE_URL` берётся из созданной Render БД автоматически. Форматы `postgres://`
и `postgresql://` нормализуются для psycopg2. `VITE_USE_MOCK=false` задан явно.
После изменения `VITE_API_URL` нужна пересборка фронтенда; внутренний адрес backend
для браузера не подходит. Превью фронтенда также требует соответствующего origin в CORS.
Промпт и JSON Schema должны присутствовать в Git и деплое рядом с README.

Проверенные источники: [x.ai structured outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs),
[x.ai image input](https://docs.x.ai/developers/model-capabilities/images/understanding),
[Render monorepo paths](https://render.com/docs/monorepo-support),
[Render Blueprint](https://render.com/docs/blueprint-spec).

## Проверка

```bash
.venv/bin/pytest -q
cd frontend
npm run build
```

Тесты не вызывают платный API: HTTP-ответ x.ai подменяется, при этом выполняются
настоящая подготовка PDF/изображений, проверка JSON, запись и чтение связанных
сущностей. Проверяются права двух пользователей, ошибки формата/ссылок, откат
транзакций, сессии, CORS, миграции и сохранение существующих пациентов.

Для проверки с настоящим Grok настройте ключ, зарегистрируйтесь, сохраните анкету,
загрузите тестовый PDF/скан и откройте оригинал, JSON и Overview. Затем войдите
другим пользователем и убедитесь, что документы первого не видны.

Ограничения MVP: синхронная обработка одного файла (по умолчанию до 10 MiB,
10 страниц PDF, изображения до 20 мегапикселей, таймаут Grok 120 секунд); нет фоновой очереди и автоматических
повторов. Повторная загрузка создаёт новый импорт без дедупликации между документами.
Сбой разбора не сохраняет исходник — его потребуется загрузить повторно.
Правильная структура JSON не гарантирует точность распознавания: сверяйте с оригиналом.
