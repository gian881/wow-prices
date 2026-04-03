import type { Notification } from '../notifications'

export type NotificationsResponse = {
  meta: {
    next_page: number | null
    total_unread: number
    total: number
  }
  data: Notification[]
}
