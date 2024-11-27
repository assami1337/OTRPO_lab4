# Запуск
## Linux/macOS:
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v $(pwd):/app assami1337/otrpo_lab3:latest

## Windows
### cmd:
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v %cd%:/app assami1337/otrpo_lab3:latest
### PowerShell:
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v ${PWD}:/app assami1337/otrpo_lab3:latest

## После выполнения контейнера файл user_id404727166.json будет создан в текущей директории.

# Просмотр файла:
## Linux/macOS:
cat user_id404727166.json

## Windows
### cmd:
type user_id404727166.json
### PowerShell:
Get-Content user_id404727166.json

# Удаление 
## Linux/macOS:
rm user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest

## Windows
### cmd:
del user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest
### PowerShell:
Remove-Item user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest

