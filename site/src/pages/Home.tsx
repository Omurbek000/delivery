/** Главная: герой с акциями, меню, как работаем, квиз, отзывы. */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { queries } from '../api/service'
import { useReveal } from '../hooks/useReveal'
import { useCountUp } from '../hooks/useCountUp'
import { PromoCarousel } from '../components/PromoCarousel'
import { DishGrid } from '../components/DishGrid'
import { DishModal } from '../components/DishModal'
import { QuizModal } from '../components/QuizModal'
import { imgUrl } from '../api/client'

const MQ = ['Суши', 'Роллы', 'Рамен', 'Вок', 'Десерты', 'Напитки', '24/7', 'Доставка 30 минут']

const CAT_EMOJI: Record<string, string> = {
  'Суши': '🍣',
  'Роллы': '🍥',
  'Напитки': '🥤',
  'Добавки': '🥢',
}

const STEPS = [
  { n: '01', h: 'Выбираешь', p: 'Листаешь неоновое меню, смотришь фото и состав, собираешь корзину.', em: '🛒' },
  { n: '02', h: 'Готовим', p: 'Кухня получает заказ мгновенно. Свежие продукты и начинка дня.', em: '🔥' },
  { n: '03', h: 'Везём', p: 'Курьер с термосумкой мчит к тебе. Статус заказа — в разделе «Мои заказы».', em: '🛵' },
  { n: '04', h: 'Кайфуешь', p: 'Горячее — горячим, холодное — холодным. Заказом останетесь довольны!', em: '😍' },
]

const REVS = [
  ['Марина К.', '👩🏻‍🦰', 'Пицца не нужна — роллы приехали за 25 минут, сырые стыки отсутствуют. Это любовь.'],
  ['Артём В.', '🧔', 'Рамен густой, насыщенный. Вкус как в Токио. Топ за свои деньги.'],
  ['Оля М.', '👩🏻', 'Сет огромный, ели втроём. Угорь тает во рту.'],
  ['Никита С.', '👨🏻‍🎤', 'Квиз угадал настроение с первого раза. Вернусь за XXL.'],
  ['Света Р.', '👩🏼', 'Чизкейк — сначала фотка в инсту, потом всё остальное. Не приторный.'],
  ['Влад Д.', '👨🏻‍💻', 'Промокод из квиза сработал на первом заказе. Мелочь, а приятно.'],
]

export default function HomePage() {
  useReveal()
  const categories = useQuery(queries.categories())
  const dishes = useQuery({ ...queries.dishes(), staleTime: 5 * 60 * 1000 })
  const promos = useQuery(queries.promos())

  const [quizOpen, setQuizOpen] = useState(false)
  const [dishId, setDishId] = useState<number | null>(null)
  const [jump, setJump] = useState<{ id: string; ts: number } | null>(null)

  /** Клик по категории в центре: скроллим к меню и включаем её фильтр. */
  function goCategory(id: number) {
    document.getElementById('menu')?.scrollIntoView({ behavior: 'smooth' })
    setJump({ id: String(id), ts: Date.now() })
  }

  const dishCount = dishes.data?.length ?? 0
  const time = useCountUp(30)
  const positions = useCountUp(dishCount)
  const rating = useCountUp(4.9, 1)

  const coverDish = promos.data?.find((p) => p.image)?.image ?? promos.data?.find((p) => p.dish?.image)?.dish?.image

  return (
    <>
      <section className="hero">
        <div className="bg-blob bb1"></div>
        <div className="bg-blob bb2"></div>
        <div className="wrap hero-grid">
          <div>
            <span className="hero-tag" data-rv>
              <i className="live"></i> Кухня работает · среднее время доставки 30 мин
            </span>
            <h1 className="big" data-rv>
              Горячо.
              <br />
              Быстро.
              <br />
              <span className="grad">Неоново.</span>
            </h1>
            <p className="hero-sub" data-rv>
              Суши из свежей рыбы, рамен на бульоне 12 часов и вок с огнём — доставка за <b>30 минут</b>.
              Пройди квиз и забери <b>промокод</b> на первый заказ.
            </p>
            <div className="hero-cta" data-rv>
              <button className="btn btn-fire" onClick={() => setQuizOpen(true)}>
                🎁 Пройти квиз
              </button>
              <a className="btn btn-neon" href="#menu">
                Смотреть меню →
              </a>
            </div>
            <div className="hero-stats" data-rv>
              <div className="hstat">
                <b className="grad">
                  <span ref={time.ref}>{time.text}</span> мин
                </b>
                <span>средняя доставка</span>
              </div>
              <div className="hstat">
                <b className="grad">
                  <span ref={positions.ref}>{positions.text}</span>+
                </b>
                <span>позиций в меню</span>
              </div>
              <div className="hstat">
                <b className="grad">4.9★</b>
                <span>
                  рейтинг · от <span ref={rating.ref}>{rating.text}</span> баллов
                </span>
              </div>
            </div>
          </div>

          <div className="hero-vis" data-rv>
            <PromoCarousel promos={promos.data ?? []} onOpenDish={(id) => setDishId(id)} />
          </div>
        </div>
      </section>

      <section id="quiz">
        <div className="wrap">
          <div className="qbanner" data-rv>
            <div>
              <h3>
                Не знаешь, чего хочется? <span className="grad">Квиз подберёт за 30 секунд</span>
              </h3>
              <p>4 вопроса о вкусе, голоде и бюджете — AI подберёт комбо из нашего меню и подскажет промокод.</p>
              <button className="btn btn-fire" onClick={() => setQuizOpen(true)}>
                🎲 Запустить квиз
              </button>
            </div>
            <div className="qb-vis">
              {coverDish ? (
                <img src={imgUrl(coverDish) ?? ''} alt="Блюдо из акции" />
              ) : (
                <div className="noimg">🎲</div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section id="cats">
        <div className="wrap shead" data-rv>
          <span className="sover">Категории</span>
          <h2 className="stitle">
            Нажми и <span className="grad">окажись там</span>
          </h2>
        </div>
        <div className="wrap">
          <div className="hcat-grid" data-rv>
            {(categories.data ?? []).map((c) => {
              const count = (dishes.data ?? []).filter((d) => d.category.id === c.id).length
              return (
                <button className="hcat" key={c.id} onClick={() => goCategory(c.id)}>
                  <span className="em">{CAT_EMOJI[c.name] ?? '🍽️'}</span>
                  <span>
                    {c.name}
                    <small>{count} {count === 1 ? 'позиция' : 'позиций'}</small>
                  </span>
                  <span className="go">→</span>
                </button>
              )
            })}
          </div>
        </div>
      </section>

      <div className="marquee" aria-hidden="true">
        <div className="mq-track">
          {(MQ.concat(MQ, MQ) as string[]).map((t, i) => (
            <span key={`${t}-${i}`}>
              {t} <i>✦</i>
            </span>
          ))}
        </div>
      </div>

      <section id="menu">
        <div className="wrap">
          <div className="shead" data-rv>
            <span className="sover">Меню</span>
            <h2 className="stitle">
              Выбирай <span className="grad">огонь</span>
            </h2>
            <p className="slead">Нажми на карточку — большие фото и полная карточка блюда.</p>
          </div>
          {dishes.isPending ? (
            <>
              <div className="filters" aria-hidden="true">
                <button className="fchip skel" tabIndex={-1}>скелет</button>
                {Array.from({ length: 3 }, (_, i) => (
                  <button className="fchip skel" tabIndex={-1} key={i}>скелет</button>
                ))}
              </div>
              <div className="pgrid" aria-hidden="true">
                {Array.from({ length: 8 }, (_, i) => (
                  <div className="dskel" key={i} />
                ))}
              </div>
            </>
          ) : (
            <DishGrid
              dishes={dishes.data ?? []}
              categories={categories.data ?? []}
              onOpen={(id) => setDishId(id)}
              jump={jump}
            />
          )}
        </div>
      </section>

      <section
        id="how"
        style={{ background: 'var(--bg2)', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}
      >
        <div className="wrap">
          <div className="shead" data-rv>
            <span className="sover">Процесс</span>
            <h2 className="stitle">
              От клика до <span className="grad">двери</span>
            </h2>
          </div>
          <div className="steps">
            {STEPS.map((s) => (
              <div className="step" data-rv key={s.n}>
                <div className="n">{s.n}</div>
                <h3>{s.h}</h3>
                <p>{s.p}</p>
                <span className="em">{s.em}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="rev" style={{ paddingTop: 0 }}>
        <div className="wrap shead" data-rv>
          <span className="sover">Отзывы</span>
          <h2 className="stitle">
            Нас уже <span className="grad">полюбили</span>
          </h2>
        </div>
        <div className="rev-wrap">
          <div className="rev-track">
            {(REVS as Array<[string, string, string]>).map((r) => (
              <div className="rev" key={r[0]}>
                <div className="rh">
                  <span className="av">{r[1]}</span>
                  <span>
                    <span className="rn">{r[0]}</span>
                    <br />
                    <span className="rs">★★★★★</span>
                  </span>
                </div>
                <p>{r[2]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <QuizModal open={quizOpen} onClose={() => setQuizOpen(false)} />
      <DishModal dishId={dishId} promos={promos.data ?? []} onClose={() => setDishId(null)} />
    </>
  )
}
