import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/app-layout'
import { ProtectedRoute } from '@/components/layout/protected-route'
import { useAuthStore } from '@/store/auth'

import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { InterviewQuestionsPage } from '@/pages/InterviewQuestionsPage'
import { QuestionDetailPage } from '@/pages/QuestionDetailPage'
import { TrainerPage } from '@/pages/TrainerPage'
import { AIInterviewChatPage } from '@/pages/AIInterviewChatPage'
import { MockInterviewPage } from '@/pages/MockInterviewPage'
import { InterviewRecordingsPage } from '@/pages/InterviewRecordingsPage'
import { SuggestionsPage } from '@/pages/SuggestionsPage'
import { TestAssignmentsPage } from '@/pages/TestAssignmentsPage'
import { TestAssignmentDetailPage } from '@/pages/TestAssignmentDetailPage'
import { HHRequirementsPage } from '@/pages/HHRequirementsPage'
import { AdminPage } from '@/pages/AdminPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export default function App() {
  const init = useAuthStore((s) => s.init)
  useEffect(() => {
    init()
  }, [init])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/interview-questions" element={<InterviewQuestionsPage />} />
        <Route path="/question/:id" element={<QuestionDetailPage />} />
        <Route path="/hh-requirements" element={<HHRequirementsPage />} />
        <Route path="/suggest" element={<SuggestionsPage />} />
        <Route path="/recordings" element={<ProtectedRoute><InterviewRecordingsPage /></ProtectedRoute>} />
        <Route path="/trainer" element={<ProtectedRoute><TrainerPage /></ProtectedRoute>} />
        <Route path="/ai-interview" element={<ProtectedRoute><AIInterviewChatPage /></ProtectedRoute>} />
        <Route path="/mock-interview" element={<ProtectedRoute><MockInterviewPage /></ProtectedRoute>} />
        <Route path="/test-assignments" element={<ProtectedRoute><TestAssignmentsPage /></ProtectedRoute>} />
        <Route path="/test-assignments/:id" element={<ProtectedRoute><TestAssignmentDetailPage /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute adminOnly><AdminPage /></ProtectedRoute>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
