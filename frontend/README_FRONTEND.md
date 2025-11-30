# Frontend - AgroSky Insight

## Быстрый запуск

### 1. Установите зависимости

```bash
npm install
```

### 2. Запустите dev сервер

```bash
npm run dev
```

Приложение запустится на http://localhost:3000

## Структура

```
frontend/
├── src/
│   ├── App.jsx          # Главный компонент
│   ├── main.jsx         # Точка входа
│   ├── components/
│   │   ├── Header.jsx   # Шапка
│   │   ├── MapView.jsx  # Карта с Leaflet
│   │   └── Sidebar.jsx  # Панель управления
│   └── index.css        # Глобальные стили
├── index.html           # HTML шаблон
├── package.json         # Зависимости
└── vite.config.js       # Конфигурация Vite
```

## Основные технологии

- **React 18** - UI библиотека
- **Leaflet.js** - интерактивная карта
- **Leaflet-Draw** - инструменты рисования
- **Axios** - HTTP клиент
- **Vite** - сборщик и dev сервер

## Сборка для продакшена

```bash
npm run build
```

Результат будет в папке `dist/`

## Линтинг

```bash
npm run lint
```


