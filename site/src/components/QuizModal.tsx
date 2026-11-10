/** Квиз: 4 вопроса → запрос к AI → подбор комбо из меню. */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { fmt, imgUrl } from '../api/client'
import { mutations, recommendQuery } from '../api/service'
import { useCart } from '../state/CartContext'
import { useToast } from '../state/ToastContext'
import { useEscape } from '../hooks/useEscape'
import type { AiRecommendResult, Dish } from '../types'

interface QuizModalProps {
  open: boolean
  onClose: () => void
}

const STEPS: Array<{ q: string; sub: string; opts: Array<{ em: string; label: string }> }> = [
  {
    q: 'Что тебя сегодня зажжёт?',
    sub: 'Шаг 1 из 4 · выбери настроение',
    opts: [
      { em: '🍣', label: 'Суши и роллы' },
      { em: '🍜', label: 'Рамен / вок' },
      { em: '🍰', label: 'Сладкое' },
      { em: '🥤', label: 'Питьё и перекус' },
      { em: '🎲', label: 'Удиви меня' },
    ],
  },
  {
    q: 'Насколько ты голоден?',
    sub: 'Шаг 2 из 4 · честно, мы не осудим',
    opts: [
      { em: '😌', label: 'Лёгкий перекус' },
      { em: '😋', label: 'Полноценный приём пищи' },
      { em: '🎉', label: 'Пир с друзьями' },
    ],
  },
  {
    q: 'Как с остротой?',
    sub: 'Шаг 3 из 4 · перец мы не жалеем',
    opts: [
      { em: '😇', label: 'Не остро' },
      { em: '🙂', label: 'Средне' },
      { em: '🔥', label: 'Огонь!' },
    ],
  },
  {
    q: 'Бюджет на заказ?',
    sub: 'Шаг 4 из 4 · подберём под кошелёк',
    opts: [
      { em: '💸', label: 'До 1000 ₽' },
      { em: '💰', label: '1000–2000 ₽' },
      { em: '💎', label: '2000+ ₽' },
    ],
  },
]

export function QuizModal({ open, onClose }: QuizModalProps) {
  const toast = useToast()
  const cart = useCart()
  const [step, setStep] = useState(-1)
  const [answers, setAnswers] = useState<string[]>([])
  const [result, setResult] = useState<AiRecommendResult | null>(null)

  const recommend = useMutation({
    mutationFn: (query: string) => mutations.aiRecommend(query),
    onSuccess: (data) => setResult(data),
    onError: (e) => {
      toast.push((e as { message?: string }).message ?? 'Не удалось подобрать', 'err')
      onClose()
    },
  })

  useEscape(open, onClose)

  if (!open) return null
  const onCloseFull = () => {
    setStep(-1)
    setAnswers([])
    setResult(null)
    onClose()
  }

  function pick(label: string) {
    const next = [...answers.slice(0, step), label]
    setAnswers(next)
    if (step < 3) {
      setStep(step + 1)
    } else {
      recommend.mutate(recommendQuery(next))
    }
  }

  const s = step >= 0 && step <= 3 ? STEPS[step] : null

  return (
    <div className="qmodal open" role="dialog" aria-modal="true" onClick={(e) => e.target === e.currentTarget && onCloseFull()}>
      <div className="qz">
        <button className="qz-close" aria-label="Закрыть квиз" onClick={onCloseFull}>✕</button>

        {result ? (
          <div className="qz-res">
            <span className="sover">Готово · твой подбор</span>
            <h3>
              Собрали тебе <span className="grad">идеальный набор</span> 🔥
            </h3>
            <div className="qz-answer">{result.answer}</div>
            {(result.dishes ?? []).map((d: Dish) => (
              <div className="qz-combo" key={d.id}>
                <div className="th">
                  {imgUrl(d.image) ? (
                    <img src={imgUrl(d.image) ?? ''} alt={d.name} />
                  ) : (
                    <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontSize: 26 }}>🍣</div>
                  )}
                </div>
                <div>
                  <div className="nm">{d.name}</div>
                  <div className="pr">{fmt(d.price)}</div>
                </div>
                <button
                  className="add"
                  aria-label={`Добавить ${d.name}`}
                  onClick={() => {
                    cart.add(d.id)
                    toast.push(`🛒 ${d.name} — в корзине`)
                  }}
                >
                  +
                </button>
              </div>
            ))}
            {result.source === 'fallback' && (
              <div className="qz-note">Сервис ещё учимся считать — подбор сделан по популярному вкусу 💛</div>
            )}
            <div className="qz-btns">
              <button
                className="btn btn-neon"
                onClick={() => {
                  result.dishes.forEach((d) => cart.add(d.id))
                  toast.push('🛒 Подбор добавлен в корзину')
                  onCloseFull()
                  cart.open()
                }}
              >
                🛒 Добавить весь подбор в корзину
              </button>
              <button
                className="btn btn-fire"
                onClick={() => {
                  setStep(0)
                  setAnswers([])
                  setResult(null)
                }}
              >
                ↺ Пройти заново
              </button>
            </div>
          </div>
        ) : recommend.isPending ? (
          <div className="qz-loading">
            <div className="spinner" />
            Собираем идеальное комбо…
          </div>
        ) : s ? (
          <>
            <span className="sover">Квиз · Онигири</span>
            <h3>{s.q}</h3>
            <p className="qsub">{s.sub}</p>
            <div className="qz-prog">
              <i style={{ width: `${(step / 4) * 100}%` }} />
            </div>
            <div className="qz-opts">
              {s.opts.map((o) => (
                <button key={o.label} className="qz-opt" onClick={() => pick(o.label)}>
                  <span className="em">{o.em}</span>
                  {o.label}
                </button>
              ))}
            </div>
            {step > 0 && (
              <button className="back-link" onClick={() => setStep(step - 1)}>
                ⬅ Назад к прошлому шагу
              </button>
            )}
          </>
        ) : (
          <>
            <span className="sover">Квиз · Онигири</span>
            <h3>Не знаешь, чего хочется?</h3>
            <p className="qsub">4 вопроса о вкусе и бюджете — AI соберёт твоё идеальное комбо.</p>
            <div className="qz-prog">
              <i style={{ width: '0%' }} />
            </div>
            <div className="qz-opts">
              <button className="qz-opt" onClick={() => setStep(0)}>
                <span className="em">🚀</span> Начать квиз
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
