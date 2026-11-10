/** Карусель акций: крутится сама, видна одна карточка, свайп и наведение. */

import { useEffect, useRef, useState } from 'react'
import { fmt, imgUrl } from '../api/client'
import type { Promo } from '../types'

interface PromoCarouselProps {
  promos: Promo[]
  onOpenDish: (dishId: number) => void
}

export function PromoCarousel({ promos, onOpenDish }: PromoCarouselProps) {
  const [active, setActive] = useState(0)
  const [manual, setManual] = useState(false)
  const stage = useRef<HTMLDivElement | null>(null)
  const swipeX = useRef<number | null>(null)

  const count = promos.length

  useEffect(() => {
    if (count <= 1) return
    if (manual) return
    const timer = setInterval(() => setActive((a) => (a + 1) % count), 4200)
    return () => clearInterval(timer)
  }, [count, manual])

  if (count === 0) {
    return (
      <div className="promos hero-promos">
        <div className="promos-top">
          <span className="t">
            <i>🔥</i> Акции и промокоды
          </span>
        </div>
        <div className="pstage" style={{ height: 180 }}>
          <div className="promo-card" data-pos="0">
            <div className="pin">
              <div className="pn">Подпишись, чтобы не пропустить</div>
              <div className="phint" style={{ marginTop: 8 }}>Скидки дня появятся здесь</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const onPointMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const el = stage.current
    if (!el) return
    if (e.pointerType === 'touch') return
    setManual(true)
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    el.style.transform = `perspective(1200px) rotateX(${-y * 3}deg) rotateY(${x * 4}deg)`
  }

  return (
    <div className="promos hero-promos">
      <div className="promos-top">
        <span className="t">
          <i>🔥</i> Акции и промокоды
        </span>
        <span className="pdots">
          {promos.map((promo, i) => (
            <button
              key={promo.id}
              className={i === active ? 'on' : ''}
              aria-label={`Акция ${i + 1}`}
              onClick={() => {
                setManual(true)
                setActive(i)
              }}
            />
          ))}
        </span>
      </div>

      <div
        ref={stage}
        className="pstage"
        onMouseMove={onPointMove}
        onMouseLeave={() => {
          stage.current?.style.setProperty('transform', '')
        }}
        onTouchStart={(e) => {
          swipeX.current = e.touches[0].clientX
        }}
        onTouchEnd={(e) => {
          if (swipeX.current === null) return
          const dx = e.changedTouches[0].clientX - swipeX.current
          if (Math.abs(dx) > 40) {
            setManual(true)
            setActive((a) => (a + (dx < 0 ? 1 : count - 1)) % count)
          }
          swipeX.current = null
        }}
      >
        {promos.map((promo, i) => {
          const pos = (i - active + count) % count
          const src = imgUrl(promo.image)
          const dishId = promo.dish?.id
          return (
            <div
              key={promo.id}
              className="promo-card"
              data-pos={pos}
              role="button"
              tabIndex={pos === 0 ? 0 : -1}
              aria-label={promo.title}
              onClick={() => {
                if (dishId) onOpenDish(dishId)
              }}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && dishId) {
                  e.preventDefault()
                  onOpenDish(dishId)
                }
              }}
            >
              <div className="pth">
                {src ? <img src={src} alt={promo.title} /> : <div className="noimg" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontSize: 60 }}>🍣</div>}
              </div>
              <div className="pin">
                <div className="pn">{promo.title}</div>
                <span className="pcode">{promo.description}</span>
                <div className="pprices">
                  <s>{fmt(promo.old_price)}</s>
                  <b>{fmt(promo.new_price)}</b>
                  <span className="pdisc">−{Math.round(Number(promo.discount_percent))}%</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
      <div className="phint">Карточки крутятся сами · показан один акция · нажми, чтобы открыть товар</div>
    </div>
  )
}
