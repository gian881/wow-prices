import type { NotificationsResponse } from '@/types/api/notifications'
import { api } from '../client'

export async function getNotifications() {
  const response = await api.get<NotificationsResponse>(`/notifications`)
  return response.data
}

export async function markNotificationsAsRead(ids: number[]) {
  const response = await api.post(`/notifications/mark-read`, ids)
  return response.data
}

export async function markNotificationAsRead(id: number | string) {
  const response = await api.post(`/notifications/${id}/mark-read`)
  return response.data
}
