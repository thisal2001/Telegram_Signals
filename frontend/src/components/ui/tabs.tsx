"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

type TabsContextValue = {
  value: string
  setValue: (val: string) => void
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
}

export function Tabs({
  value,
  defaultValue,
  onValueChange,
  className,
  children,
  ...props
}: TabsProps) {
  const isControlled = value !== undefined
  const [internalValue, setInternalValue] = React.useState<string>(defaultValue ?? "")
  const currentValue = isControlled ? (value as string) : internalValue

  const setValue = React.useCallback(
    (val: string) => {
      if (!isControlled) {
        setInternalValue(val)
      }
      onValueChange?.(val)
    },
    [isControlled, onValueChange]
  )

  const ctx = React.useMemo(() => ({ value: currentValue, setValue }), [currentValue, setValue])

  return (
    <TabsContext.Provider value={ctx}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

export const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} role="tablist" className={cn("inline-flex items-center gap-2", className)} {...props} />
  )
)
TabsList.displayName = "TabsList"

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, ...props }, ref) => {
    const ctx = React.useContext(TabsContext)
    if (!ctx) throw new Error("TabsTrigger must be used within Tabs")
    const isActive = ctx.value === value
    return (
      <button
        ref={ref}
        role="tab"
        aria-selected={isActive}
        data-state={isActive ? "active" : "inactive"}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/50",
          className
        )}
        onClick={(e) => {
          props.onClick?.(e)
          ctx.setValue(value)
        }}
        {...props}
      />
    )
  }
)
TabsTrigger.displayName = "TabsTrigger"

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, children, ...props }, ref) => {
    const ctx = React.useContext(TabsContext)
    if (!ctx) throw new Error("TabsContent must be used within Tabs")
    const isActive = ctx.value === value
    return (
      <div
        ref={ref}
        role="tabpanel"
        hidden={!isActive}
        className={cn(className)}
        {...props}
      >
        {isActive ? children : null}
      </div>
    )
  }
)
TabsContent.displayName = "TabsContent"


