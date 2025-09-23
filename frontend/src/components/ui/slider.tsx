"use client"

import * as React from "react"

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
}

export function Slider({ value, onValueChange, min = 0, max = 100, step = 1, ...props }: SliderProps) {
  return (
    <input
      type="range"
      value={value[0]}
      min={min}
      max={max}
      step={step}
      onChange={(e) => onValueChange([Number(e.target.value)])}
      {...props}
    />
  )
}


