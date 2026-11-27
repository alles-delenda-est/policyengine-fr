import { useId, useState } from 'react'

export default function InfoPopover({ label, doc, reference }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  if (!doc && !reference) return null

  return (
    <span className="pe-info">
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
