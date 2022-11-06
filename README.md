# Homework-bot - бот-ассистент.


**Telegram-бот**, который обращается к API сервиса Практикум.Домашка и узнает статус домашней работы:
- раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

```
Python 3.8
python-dotenv 0.19.0
python-telegram-bot 13.7
```

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:shlenskov/Homework-bot-Telegram.git
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

> для MacOS:

```
python3 -m venv env

source venv/bin/activate 
```
  
> для Windows:

```
python -m venv venv

source venv/bin/activate

source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Записать в переменные окружения (файл .env) необходимые ключи:

```
токен профиля на Яндекс.Практикуме
токен телеграм-бота
свой ID в телеграме
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
