# Клонирование репозитория
```
git clone https://github.com/assami1337/OTRPO_lab4.git && cd OTRPO_lab4
```
# Создание виртуального окружения
```
python3 -m venv venv
```
# Активация виртуального окружения
```
source venv/bin/activate || venv\Scripts\activate
```
# Установка зависимостей
```
pip install -r requirements.txt
```
# Настройка переменных окружения
```
cp .env.example .env
```
# Редактируйте файл .env, добавив необходимые данные:
```
# TOKEN=<токен доступа VK API>
# USER_ID=<ID пользователя для анализа>
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=<пароль Neo4j>
# MAX_DEPTH=<максимальная глубина анализа, например 3>
```

# Запуск программы
```
python main.py --user_id <ID_ПОЛЬЗОВАТЕЛЯ> --max_depth <ГЛУБИНА>
```
