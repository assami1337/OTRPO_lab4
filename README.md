# Запуск
## Linux/macOS:
```bash
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v $(pwd):/app assami1337/otrpo_lab3:latest
```
## Windows
### cmd:
```cmd
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v %cd%:/app assami1337/otrpo_lab3:latest
```
### PowerShell:
```powershell
docker run --rm -e TOKEN=<ВАШ_ТОКЕН> -v ${PWD}:/app assami1337/otrpo_lab3:latest
```
## После выполнения контейнера файл user_id404727166.json будет создан в текущей директории.

# Просмотр файла:
## Linux/macOS:
```bash
cat user_id404727166.json
```
## Windows
### cmd:
```cmd
type user_id404727166.json
```
### PowerShell:
```powershell
Get-Content user_id404727166.json
```
# Удаление 
## Linux/macOS:
```bash
rm user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest
```
## Windows
### cmd:
```cmd
del user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest
```
### PowerShell:
```powershell
Remove-Item user_id404727166.json
docker rmi assami1337/otrpo_lab3:latest
```
