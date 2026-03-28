import type { ClassValue } from 'clsx'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function numberOfDaysToMonthOrDays(days: number | string): {
  value: number
  unit: 'days' | 'months'
} {
  if (typeof days === 'string') {
    if (days === 'all') {
      return {
        value: 0,
        unit: 'days',
      }
    }
    days = parseInt(days, 10)
  }
  if (days % 30 === 0) {
    return {
      value: days / 30,
      unit: 'months',
    }
  }
  return {
    value: days,
    unit: 'days',
  }
}

export function valueUnitToDays(value: number | string, unit: 'days' | 'months') {
  if (unit === 'months') {
    const valueNumber = typeof value === 'string' ? parseInt(value, 10) : value
    return String(valueNumber * 30)
  }

  return String(value)
}
