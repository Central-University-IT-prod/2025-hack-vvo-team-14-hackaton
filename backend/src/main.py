from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
from datetime import datetime

app = FastAPI(
    title="Sports Competitions API",
    version="1.0.0",
    root_path="/api",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Модели данных
class Competition(BaseModel):
    id: int
    title: str
    sport: str
    date: str
    participantsCount: int
    image: str

class Metadata(BaseModel):
    totalCompetitions: int
    lastUpdated: datetime

class PageData(BaseModel):
    pageTitle: str
    competitions: List[Competition]
    metadata: Metadata

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: str  # "participant" или "organizer"

class UserCreate(UserBase):
    password: str
    full_name: str
    post: Optional[str] = None  # Для организаторов

class User(UserBase):
    id: int
    full_name: str
    post: Optional[str] = None

# Данные из JSON
data = {
    "pageTitle": "Главная страница",
    "competitions": [
        {
            "id": 1,
            "title": "Чемпионат по футболу 2023",
            "sport": "Футбол",
            "date": "2023-11-15",
            "participantsCount": 32,
            "image": "football.jpg"
        },
        {
            "id": 2,
            "title": "Кубок по баскетболу",
            "sport": "Баскетбол",
            "date": "2023-11-25",
            "participantsCount": 24,
            "image": "basketball.jpg"
        }
    ],
    "metadata": {
        "totalCompetitions": 2,
        "lastUpdated": "2023-11-01T14:30:00Z"
    }
}

# "База данных" пользователей
users_db = []
current_id = 1

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/api/docs")

# HTML формы для регистрации и входа
@app.get("/login-form", response_class=HTMLResponse, include_in_schema=False)
async def login_form():
    return """
    <html>
        <head>
            <title>Вход</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto; padding: 20px; }
                form { display: flex; flex-direction: column; gap: 10px; }
                input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
                button { padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #45a049; }
                .form-footer { margin-top: 15px; text-align: center; }
            </style>
        </head>
        <body>
            <h2>Вход в систему</h2>
            <form action="/api/login" method="post">
                <label>Почта или номер телефона:</label>
                <input type="text" name="login" required placeholder="Введите email или телефон">
                
                <label>Пароль:</label>
                <input type="password" name="password" required placeholder="Введите пароль">
                
                <button type="submit">Войти</button>
            </form>
            <div class="form-footer">
                <p>Ещё нет аккаунта? <a href="/api/register-form">Зарегистрироваться</a></p>
            </div>
        </body>
    </html>
    """

# API эндпоинты
@app.post("/register", tags=["auth"])
async def register(
    full_name: str = Form(...),
    username: str = Form(...),
    email: EmailStr = Form(...),
    phone: Optional[str] = Form(None),
    password: str = Form(...),
    role: str = Form(...),
    post: Optional[str] = Form(None)
):
    """Регистрация нового пользователя"""
    global current_id
    
    # Проверка уникальности email и username
    if any(u.email == email for u in users_db):
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    if any(u.username == username for u in users_db):
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    
    # Проверка роли
    if role not in ["participant", "organizer"]:
        raise HTTPException(status_code=400, detail="Некорректная роль")
    
    # Проверка пароля
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 8 символов")
    
    # Для организаторов проверяем наличие должности
    if role == "organizer" and not post:
        raise HTTPException(status_code=400, detail="Для организатора требуется указать должность")
    
    new_user = User(
        id=current_id,
        username=username,
        email=email,
        phone=phone,
        role=role,
        full_name=full_name,
        post=post if role == "organizer" else None
    )
    
    # В реальном приложении здесь должно быть хеширование пароля!
    users_db.append({"user": new_user, "password": password})
    current_id += 1
    
    return {"message": "Пользователь успешно зарегистрирован", "user_id": new_user.id}

@app.post("/login", tags=["auth"])
async def login(login: str = Form(...), password: str = Form(...)):
    """Вход в систему по email или телефону"""
    # Поиск пользователя по email или телефону
    user_data = None
    for user_entry in users_db:
        user = user_entry["user"]
        if (login == user.email or login == user.phone) and password == user_entry["password"]:
            user_data = user
            break
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    
    return {
        "message": "Вход выполнен успешно",
        "user_id": user_data.id,
        "username": user_data.username,
        "role": user_data.role
    }

# Остальные эндпоинты из предыдущей версии
@app.get("/page", response_model=PageData, tags=["page"])
async def get_page_data():
    """Получить все данные для главной страницы"""
    return data

@app.get("/competitions", response_model=List[Competition], tags=["competitions"])
async def get_all_competitions():
    """Получить список всех соревнований"""
    return data["competitions"]

@app.get("/competitions/{competition_id}", response_model=Competition, tags=["competitions"])
async def get_competition(competition_id: int):
    """Получить информацию о конкретном соревновании по ID"""
    for competition in data["competitions"]:
        if competition["id"] == competition_id:
            return competition
    raise HTTPException(status_code=404, detail="Competition not found")

@app.get("/metadata", response_model=Metadata, tags=["metadata"])
async def get_metadata():
    """Получить метаданные"""
    return data["metadata"]

# Добавляем новую модель данных для матчей
class Match(BaseModel):
    id: int
    competition_id: int
    team1: str
    team2: str
    date: str
    time: str
    venue: str

# Добавляем данные о матчах
matches_data = [
    {
        "id": 1,
        "competition_id": 1,
        "team1": "Команда А",
        "team2": "Команда B",
        "date": "2023-11-15",
        "time": "15:00",
        "venue": "Стадион Центральный"
    },
    {
        "id": 2,
        "competition_id": 1,
        "team1": "Команда C",
        "team2": "Команда D",
        "date": "2023-11-16",
        "time": "17:00",
        "venue": "Стадион Северный"
    },
    {
        "id": 3,
        "competition_id": 2,
        "team1": "Баскетбольные звезды",
        "team2": "Космические джемы",
        "date": "2023-11-25",
        "time": "18:30",
        "venue": "Дворец спорта"
    }
]

# Добавляем новый эндпоинт для получения матчей по ID соревнования
@app.get("/competitions/{competition_id}/matches", response_model=List[Match], tags=["competitions"])
async def get_competition_matches(competition_id: int):
    """Получить список матчей для конкретного соревнования"""
    matches = [match for match in matches_data if match["competition_id"] == competition_id]
    if not matches:
        raise HTTPException(status_code=404, detail="No matches found for this competition")
    return matches

# Добавляем HTML страницу для просмотра матчей соревнования
@app.get("/competitions/{competition_id}/matches-page", response_class=HTMLResponse, include_in_schema=False)
async def competition_matches_page(competition_id: int):
    """HTML страница с матчами соревнования"""
    # Находим соревнование
    competition = None
    for comp in data["competitions"]:
        if comp["id"] == competition_id:
            competition = comp
            break
    
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Находим матчи для этого соревнования
    matches = [match for match in matches_data if match["competition_id"] == competition_id]
    
    # Генерируем HTML
    matches_html = ""
    for match in matches:
        matches_html += f"""
        <div class="match-card">
            <h3>{match['team1']} vs {match['team2']}</h3>
            <p>Дата: {match['date']}</p>
            <p>Время: {match['time']}</p>
            <p>Место: {match['venue']}</p>
        </div>
        """
    
    return f"""
    <html>
        <head>
            <title>Матчи {competition['title']}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .competition-header {{
                    background-color: #f5f5f5;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .match-card {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                .match-card h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                }}
                .back-button {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 15px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .back-button:hover {{
                    background-color: #2980b9;
                }}
            </style>
        </head>
        <body>
            <div class="competition-header">
                <h1>{competition['title']}</h1>
                <p>Спорт: {competition['sport']}</p>
                <p>Дата проведения: {competition['date']}</p>
            </div>
            
            <h2>Матчи турнира</h2>
            
            {matches_html if matches else "<p>Матчи еще не добавлены</p>"}

<a href="/api/competitions" class="back-button">Вернуться к списку соревнований</a>
        </body>
    </html>
    """

# Обновляем HTML для списка соревнований, чтобы добавить кнопки просмотра матчей
@app.get("/competitions-page", response_class=HTMLResponse, include_in_schema=False)
async def competitions_page():
    """HTML страница со списком всех соревнований"""
    competitions_html = ""
    for comp in data["competitions"]:
        competitions_html += f"""
        <div class="competition-card">
            <h2>{comp['title']}</h2>
            <p>Спорт: {comp['sport']}</p>
            <p>Дата: {comp['date']}</p>
            <p>Участников: {comp['participantsCount']}</p>
            <a href="/api/competitions/{comp['id']}/matches-page" class="view-matches-button">Просмотреть матчи</a>
        </div>
        """
    
    return f"""
    <html>
        <head>
            <title>Список соревнований</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .competition-card {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .view-matches-button {{
                    display: inline-block;
                    padding: 8px 12px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .view-matches-button:hover {{
                    background-color: #2980b9;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 30px;
                }}
                .home-button {{
                    padding: 8px 12px;
                    background-color: #2ecc71;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Список соревнований</h1>
                <a href="/api" class="home-button">На главную</a>
            </div>
            
            {competitions_html}
        </body>
    </html>
    """