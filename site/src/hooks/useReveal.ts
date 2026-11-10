/** Появление секций с data-rv при скролле. */

import { useEffect } from 'react'

export function useReveal() {
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add('in')
            io.unobserve(en.target)
          }
        }),
      { threshold: 0.14 },
    )
    document.querySelectorAll('[data-rv]').forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
}
