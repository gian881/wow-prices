import type { SettingsResponse } from '@/types/api/settings'
import type { Setting } from '@/types/settings'
import { api } from '../client'

export async function getAllSettings() {
  const response = await api.get<SettingsResponse>('/settings/')
  return response.data
}

export async function updateSetting(key: string, value: string) {
  const response = await api.put<Setting>(`/settings/${key}/`, null, {
    params: { value },
  })
  return response.data
}
