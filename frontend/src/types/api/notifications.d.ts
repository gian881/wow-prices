import type { Notification } from '../notifications'

export type NotificationsResponse = {
  meta: {
    page: number
    limit: number
    total: number
    max_page: number
  }
  data: Notification[]
}
