/** Общая логика плавающих кнопок: перетаскивание, запоминание позиции, клик-открытие. */

import { useEffect, useRef, useState, type CSSProperties } from 'react'
import type { PointerEvent as RPointerEvent, RefObject } from 'react'

const PAD = 12

interface DragFab {
  style: CSSProperties | undefined
  handlers: {
    onPointerDown: (e: RPointerEvent<HTMLElement>) => void
    onPointerMove: (e: RPointerEvent<HTMLElement>) => void
    onPointerUp: () => void
    onPointerCancel: () => void
  }
}

export function useDragFab(storageKey: string, onOpen: () => void, ref: RefObject<HTMLElement | null>): DragFab {
  const drag = useRef({ active: false, moved: false, sx: 0, sy: 0, id: -1 })
  const [pos, setPos] = useState<{ x: number; y: number } | null>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem(storageKey) ?? 'null') as { x?: number; y?: number } | null
      if (!raw || typeof raw.x !== 'number' || typeof raw.y !== 'number') return null
      return { x: raw.x * window.innerWidth, y: raw.y * window.innerHeight }
    } catch {
      return null
    }
  })

  useEffect(() => {
    const onResize = () =>
      setPos((p) => {
        if (!p) return p
        const el = ref.current
        const ew = el?.offsetWidth ?? 150
        const eh = el?.offsetHeight ?? 52
        return {
          x: Math.min(Math.max(PAD, p.x), Math.max(PAD, window.innerWidth - ew - PAD)),
          y: Math.min(Math.max(PAD, p.y), Math.max(PAD, window.innerHeight - eh - PAD)),
        }
      })
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [ref])

  function down(e: RPointerEvent<HTMLElement>) {
    if (e.button !== 0) return
    drag.current = { active: true, moved: false, sx: e.clientX, sy: e.clientY, id: e.pointerId }
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  function move(e: RPointerEvent<HTMLElement>) {
    if (!drag.current.active || e.pointerId !== drag.current.id) return
    if (!drag.current.moved && Math.hypot(e.clientX - drag.current.sx, e.clientY - drag.current.sy) < 7) return
    drag.current.moved = true
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    setPos({
      x: Math.min(Math.max(PAD, e.clientX - r.width / 2), window.innerWidth - r.width - PAD),
      y: Math.min(Math.max(PAD, e.clientY - r.height / 2), window.innerHeight - r.height - PAD),
    })
  }

  function up() {
    const wasDrag = drag.current.moved
    drag.current.active = false
    if (!wasDrag) {
      onOpen()
      return
    }
    setPos((p) => {
      if (!p) return p
      localStorage.setItem(storageKey, JSON.stringify({ x: p.x / window.innerWidth, y: p.y / window.innerHeight }))
      return p
    })
  }

  const style = pos ? { left: pos.x, top: pos.y, right: 'auto', bottom: 'auto' } : undefined
  return {
    style,
    handlers: { onPointerDown: down, onPointerMove: move, onPointerUp: up, onPointerCancel: up },
  }
}
