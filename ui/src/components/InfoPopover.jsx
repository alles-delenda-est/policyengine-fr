import { useEffect, useId, useRef, useState } from 'react'

export default function InfoPopover({ label, doc, reference }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const containerRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    const handleMouseDown = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('keydown', handleKey)
    document.addEventListener('mousedown', handleMouseDown)
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [open])

  if (!doc && !reference) return null

  return (
    <span ref={containerRef} className="pe-info">
      <button
        type="button"
        className="pe-info-btn"
        aria-expanded={open}
        aria-controls={id}
        aria-label={`Détail légal : ${label}`}
        onClick={() => setOpen((o) => !o)}
      >
        i
      </button>
      {open && (
        <span id={id} role="note" className="pe-info-popover">
          {doc && <span className="pe-info-doc">{doc}</span>}
          {reference && (
            <a
              href={reference}
              target="_blank"
              rel="noopener noreferrer"
              className="pe-info-link"
            >
              Source officielle (Légifrance / Service-Public) ↗
            </a>
          )}
        </span>
      )}
    </span>
  )
}
