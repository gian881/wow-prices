import type { GoldAndSilver, Intent, Quality, Rarity } from '.'

type BaseItem = {
  id: number
  name: string
  image: string
  price: GoldAndSilver
  quality: Quality
  rarity: Rarity
  intent: Intent
  notify_sell: boolean
  notify_buy: boolean
  is_active: boolean
}

export type Item = BaseItem

export type TodayItem = {
  hour: string
  items: Item[]
}[]

export type WeekItem = {
  weekday: string
  hours: {
    hour: number
    items: {
      id: number
      name: string
      price: GoldAndSilver
      quality: Quality
      rarity: Rarity
      image: string
    }[]
  }[]
}

export type DetailedItem = BaseItem & {
  quantity_threshold: number
  above_alert: GoldAndSilver
  below_alert: GoldAndSilver
  current_quantity: number
  current_price: GoldAndSilver
  last_timestamp: string
  selling: {
    weekday: string
    hour: number
    price: GoldAndSilver
    price_diff: GoldAndSilver & {
      sign: string
    }
  } | null
  buying: {
    weekday: string
    hour: number
    price: GoldAndSilver
    price_diff: GoldAndSilver & {
      sign: string
    }
  } | null
}

export type ItemPlotData = {
  average_price_data: {
    x: string[]
    y: string[]
    z: number[][]
  }
  average_quantity_data: {
    x: string[]
    y: string[]
    z: number[][]
  }
  last_week_data: {
    price: {
      x: string[]
      y: number[]
    }
    quantity: {
      x: string[]
      y: number[]
    }
  }
}
