export type Notification = {
  id: number
  type:
    | 'price_above_alert'
    | 'price_below_alert'
    | 'price_above_best_avg_alert'
    | 'price_below_best_avg_alert'
  price_diff: {
    gold: number
    silver: number
  }
  current_price: {
    gold: number
    silver: number
  }
  price_threshold: {
    gold: number
    silver: number
  } | null
  item: {
    id: number
    name: string
    image: string
    quality: number
    rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  }
  read: boolean
  created_at: string
}

export type Item = {
  id: number
  name: string
  price: {
    gold: number
    silver: number
  }
  quality: number
  image: string
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  intent: 'buy' | 'sell' | 'both'
  notify_sell: boolean
  notify_buy: boolean
}
