import type { NotificationsResponse } from '@/types/api/notifications'
import { api } from '../client'

export async function getNotifications(
  ignoreRead: boolean = false,
  page: number = 1,
  limit: number = 10,
) {
  const response = await api.get<NotificationsResponse>(`/notifications/`, {
    params: {
      ignore_read: ignoreRead,
      page,
      limit,
    },
  })
  return response.data
}

export async function markAllNotificationsAsRead() {
  const response = await api.post(`/notifications/mark-all-read`)
  return response.data
}

export async function markNotificationAsRead(id: number | string) {
  const response = await api.post(`/notifications/${id}/mark-read`)
  return response.data
}
