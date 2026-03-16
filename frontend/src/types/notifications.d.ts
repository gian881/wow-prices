type NotificationType =
  | 'price_above_alert'
  | 'price_below_alert'
  | 'price_above_best_avg_alert'
  | 'price_below_best_avg_alert'

export type Notification = {
  id: number
  type: NotificationType
  price_diff: GoldAndSilver
  current_price: GoldAndSilver
  price_threshold: GoldAndSilver | null
  item: Pick<Item, 'id' | 'name' | 'image' | 'quality' | 'rarity'>
  read: boolean
  created_at: string
}
