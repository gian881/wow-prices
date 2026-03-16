import { api } from '@/services/api/client'
import type {
  CreateItemRequest,
  DetailedItemResponse,
  GetItemsParams,
  ItemPlotDataResponse,
  TodayItemsResponse,
  UpdateItemRequest,
  WeekItemsResponse,
} from '@/types/api/item'
import type { Item } from '@/types/item'

export async function getItem(id: string | number | string[]) {
  if (Array.isArray(id)) {
    id = id[0]
  }

  const response = await api.get<DetailedItemResponse>(`/items/${id}`)
  return response.data
}

export async function getItemPlotData(id: string | number | string[]) {
  if (Array.isArray(id)) {
    id = id[0]
  }

  const response = await api.get<ItemPlotDataResponse>(`/items/${id}/plot-data`)
  return response.data
}

export async function getItems(params?: GetItemsParams) {
  const response = await api.get<Item[]>('/items', {
    params,
  })

  return response.data
}

export async function lookupItem(id: string | number | string[]) {
  const response = await api.get<Pick<Item, 'id' | 'name' | 'image' | 'quality' | 'rarity'> | null>(
    `/items/${id}/lookup`,
  )

  return response.data
}

export async function getTodayItems() {
  const response = await api.get<TodayItemsResponse>('/items/today')

  return response.data
}

export async function getWeekItems() {
  const response = await api.get<WeekItemsResponse>('/items/week')
  return response.data
}

export async function createItem(item: CreateItemRequest) {
  const response = await api.post(`/items/${item.id}`, item)

  return response.data
}

export async function editItem(id: number | string | string[], dataToUpdate: UpdateItemRequest) {
  if (Array.isArray(id)) {
    id = id[0]
  }

  const response = await api.put(`/items/${id}`, dataToUpdate)
  return response.data
}
