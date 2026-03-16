import type { DetailedItem, ItemPlotData, TodayItem, WeekItem } from '@/types/item'
import type { Intent, Quality } from '..'

export type CreateItemRequest = {
  id: number
  name: string
  image: string
  quality: Quality
  rarity: Rarity
  intent: Intent
  notifySell: boolean
  notifyBuy: boolean
  quantityThreshold: number
  aboveAlert: GoldAndSilver
  belowAlert: GoldAndSilver
}

export type UpdateItemRequest = {
  intent?: Intent
  notify_sell?: boolean
  notify_buy?: boolean
  quantity_threshold?: number
  above_alert?: GoldAndSilver
  below_alert?: GoldAndSilver
  is_active?: boolean
  quality?: Quality
}

export type DetailedItemResponse = DetailedItem

export type ItemPlotDataResponse = ItemPlotData

export type GetItemsParams = {
  order_by?: 'id' | 'name' | 'price' | 'quality' | 'rarity'
  order?: 'desc' | 'asc'
  intent?: Intent
  show_inactive?: boolean
}

export type TodayItemsResponse = TodayItem[]

export type WeekItemsResponse = WeekItem[]
