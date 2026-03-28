import { apiClient, getUserSession } from './base'

export const chatApi = {
  // Start new interview chat
  startInterviewChat: (topic, difficulty) =>
    apiClient.post('/api/interview-chat/start', {
      topic,
      difficulty,
      user_session: getUserSession()
    }),

  // Send message in chat
  sendChatMessage: (interviewId, message) =>
    apiClient.post(`/api/interview-chat/${interviewId}/message`, {
      message,
      user_session: getUserSession()
    }),

  // End interview and get summary
  endInterviewChat: (interviewId) =>
    apiClient.post(`/api/interview-chat/${interviewId}/end`, {
      user_session: getUserSession()
    }),

  // Get interview history
  getInterviewHistory: (limit = 10) =>
    apiClient.get('/api/interview-chat/history', {
      params: {
        user_session: getUserSession(),
        limit
      }
    })
}
