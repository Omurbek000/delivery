/** Футер сайта: лого, навигация, контакты. */

import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer id="contacts">
      <div className="wrap">
        <div className="fgrid2">
          <div>
            <Link to="/" className="logo" style={{ marginBottom: 14 }}>
              <span className="logo-box">🍣</span>
              <span>
                Онигири
                <small>доставка еды 24/7</small>
              </span>
            </Link>
            <p style={{ color: 'var(--muted)', fontSize: 14, maxWidth: 300 }}>
              Неоновая кухня: суши и роллы, рамен, вок и десерты. Готовим и возим по всему городу круглосуточно.
            </p>
            <div className="fsoc">
              <a href="#menu" aria-label="Смотреть меню">🍱</a>
              <a href="#quiz" aria-label="Пройти квиз">🎲</a>
              <a href="#rev" aria-label="Отзывы">⭐</a>
            </div>
          </div>
          <div className="flinks">
            <h4>Навигация</h4>
            <a href="#menu">Меню</a>
            <a href="#how">Как это работает</a>
            <a href="#quiz">Квиз</a>
            <a href="#rev">Отзывы</a>
            <Link to="/orders">Мои заказы</Link>
          </div>
          <div className="flinks">
            <h4>Контакты</h4>
            <span>Статус заказа — в разделе «Мои заказы»</span>
            <span>Доставка за 30 минут по всему городу</span>
            <span>Работаем 24/7</span>
          </div>
        </div>
        <div className="fbot">
          <span>© 2026 Онигири. Сделано с огнём 🔥</span>
          <span>Оплата: картой, СБП, наличными курьеру</span>
        </div>
      </div>
    </footer>
  )
}
