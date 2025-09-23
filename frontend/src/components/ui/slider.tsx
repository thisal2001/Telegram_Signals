"use client"

import * as React from "react"

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'defaultValue'> {
    value: number[]
    onValueChange: (value: number[]) => void
    min?: number
    max?: number
    step?: number
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
    ({ className, value, onValueChange, min = 0, max = 100, step = 1, ...props }, ref) => {
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            const newValue = [parseFloat(e.target.value)]
            onValueChange(newValue)
        }

        return (
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value[0] || min}
                onChange={handleChange}
                className={`flex w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${className || ''}`}
                ref={ref}
                {...props}
            />
        )
    }
)

Slider.displayName = "Slider"

export { Slider }