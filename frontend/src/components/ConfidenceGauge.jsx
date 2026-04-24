import { useState, useEffect } from 'react'

export default function ConfidenceGauge({ confidence, label, id = 'gauge' }) {
  const [animated, setAnimated] = useState(0)

  useEffect(() => {
    setAnimated(0)
    const t = setTimeout(() => setAnimated(confidence), 80)
    return () => clearTimeout(t)
  }, [confidence])

  const r = 62
  const cx = 80
  const cy = 80
  const circumference = Math.PI * r
  const filled = (animated / 100) * circumference

  const isUrgent = label === 'urgent'
  const color = isUrgent ? '#ff5757' : label === 'normal' ? '#22d98a' : '#7c6eff'

  return (
    <div className="gauge-container">
      <svg viewBox="0 0 160 90" className="gauge-svg">
        <defs>
          <filter id={`glow-${id}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="var(--surface3)"
          strokeWidth="11"
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="11"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          filter={`url(#glow-${id})`}
          style={{ transition: 'stroke-dasharray 1.1s cubic-bezier(.4,0,.2,1)' }}
        />
        {/* Center value */}
        <text
          x={cx}
          y={cy - 8}
          textAnchor="middle"
          fill={color}
          fontSize="22"
          fontWeight="700"
          fontFamily="Inter, system-ui, sans-serif"
        >
          {animated.toFixed(0)}%
        </text>
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          fill="var(--text-dim)"
          fontSize="10"
          fontFamily="Inter, system-ui, sans-serif"
        >
          confidence
        </text>
      </svg>
    </div>
  )
}
