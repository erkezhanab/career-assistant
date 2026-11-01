// Точка входа React-приложения — файл, с которого всё начинается.
//
// Браузер загружает public/index.html, где есть пустой <div id="root">.
// Этот файл помещает в него React-приложение.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Находим в HTML элемент с id="root" и создаём в нём React-приложение
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  // StrictMode — режим строгой проверки: во время разработки
  // предупреждает об устаревших приёмах и ошибках в коде.
  // В собранной версии приложения не влияет на работу
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// Измерение скорости загрузки страницы. Без аргумента ничего
// не выводит — данные можно отправить в аналитику при необходимости
reportWebVitals();
