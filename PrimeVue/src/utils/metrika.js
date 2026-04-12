import { API_BASE_URL, getUserSession } from '../api/base'

const sendEvent = (eventName, params = {}) => {
  if (!eventName || typeof window === 'undefined') return

  const userSession = getUserSession()
  if (!userSession) return

  fetch(`${API_BASE_URL}/analytics/event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_session: userSession,
      event_name: eventName,
      params
    }),
    keepalive: true
  }).catch(() => {})
}

// Kept for backward compatibility in existing imports.
export const trackMetrikaHit = () => {}

export const trackMetrikaGoal = (goal, params = {}) => {
  sendEvent(goal, params)
}
