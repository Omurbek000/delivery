/** Плавающая кнопка AI-подбора: всегда на экране, перетаскивается, открывает квиз. */

import { useRef, useState } from 'react'
import { useDragFab } from '../hooks/useDragFab'
import { QuizModal } from './QuizModal'

export function AiFab() {
  const ref = useRef<HTMLButtonElement>(null)
  const [open, setOpen] = useState(false)
  const { style, handlers } = useDragFab('onigiri-fab-pos-ai', () => setOpen(true), ref)

  return (
    <>
      <button ref={ref} type="button" className="aifab" style={style} {...handlers} aria-label="AI-подбор блюд">
        <span className="ai-i" aria-hidden="true">🤖</span>
        <span className="ai-t">AI-подбор</span>
      </button>
      <QuizModal open={open} onClose={() => setOpen(false)} />
    </>
  )
}
