export const navItems = [
  { label: 'Вопросы', to: '/interview-questions' },
  { label: 'Тренажёр', to: '/trainer' },
  { label: 'AI Interview', to: '/ai-interview' },
  { label: 'Задания', to: '/test-assignments' },
  { label: 'Навыки', to: '/hh-requirements' },
  { label: 'Записи', to: '/recordings' },
  { label: 'Админ', to: '/admin' }
]

export const questions = [
  ['Почему вы выбрали именно нашу компанию?', 'Общие вопросы', 'junior', 100, 'Задают почти всегда', 'pi-comments'],
  ['Чем вы занимаетесь на текущем месте работы?', 'Общие вопросы', 'junior', 100, 'Задают почти всегда', 'pi-briefcase'],
  ['Какой опыт работы у вас с React?', 'Технические', 'junior', 92, 'Очень часто', 'pi-code'],
  ['Расскажите о вашем опыте работы с базами данных.', 'Технические', 'junior', 86, 'Часто встречается', 'pi-database'],
  ['Сколько технических багов вы исправляли за последний проект?', 'Поведенческие', 'junior', 64, 'Средняя частота', 'pi-users'],
  ['У вас есть опыт работы в международных командах?', 'Поведенческие', 'junior', 58, 'Иногда встречается', 'pi-globe']
].map((item, index) => ({
  id: index + 1,
  title: item[0],
  topic: item[1],
  level: item[2],
  probability: item[3],
  frequency: item[4],
  icon: item[5]
}))

export const recordings = [
  ['Собеседование на Backend Developer', 'Backend Developer', '54:32', '23 мая 2025'],
  ['Python Developer Interview', 'Python Developer', '48:11', '22 мая 2025'],
  ['Frontend Developer Interview', 'Frontend Developer', '1:12:09', '21 мая 2025'],
  ['DevOps Engineer Interview', 'DevOps Engineer', '45:07', '20 мая 2025'],
  ['System Analyst Interview', 'System Analyst', '1:05:34', '19 мая 2025'],
  ['QA Engineer Interview', 'QA Engineer', '51:48', '18 мая 2025'],
  ['Data Analyst Interview', 'Data Analyst', '44:21', '17 мая 2025'],
  ['Product Manager Interview', 'Product Manager', '55:03', '16 мая 2025']
].map((item, index) => ({ id: index + 1, title: item[0], role: item[1], duration: item[2], date: item[3] }))

export const extractedQuestions = [
  ['Чем вы занимаетесь на текущем месте работы?', 'junior'],
  ['Почему вы выбрали именно нашу компанию?', 'junior'],
  ['Сколько лет опыта работы?', 'junior'],
  ['Назовите ваш любимый цвет.', 'junior'],
  ['Почему капитализированные ключи крутые?', 'middle'],
  ['На каких языках вы писали код?', 'junior'],
  ['Вы писали код на Паскале?', 'junior'],
  ['Как вы относитесь к Фортрану?', 'junior'],
  ['Вы писали на Лиспе?', 'junior'],
  ['Вы писали на Бейсике?', 'junior'],
  ['Вы писали на Алголе?', 'junior'],
  ['Какие фреймворки вы использовали в проектах?', 'middle']
].map((item, index) => ({ id: index + 1, title: item[0], level: item[1] }))

export const assignments = [
  ['Создать To-Do приложение на React', 'Яндекс', 'Я', 'Frontend разработчик', 'junior', ['React', 'JavaScript', 'CSS'], 'Реализовать список задач с фильтрацией, CRUD операциями и сохранением в localStorage.'],
  ['REST API на Spring Boot', 'СБЕР', '✓', 'Java разработчик', 'middle', ['Java', 'Spring Boot', 'PostgreSQL', 'JWT'], 'Разработать REST API для управления пользователями и JWT авторизацией.'],
  ['Микросервисная архитектура', 'VK', 'vk', 'Backend разработчик', 'senior', ['Docker', 'Kubernetes', 'gRPC', 'PostgreSQL'], 'Спроектировать и реализовать систему из 3 микросервисов с API Gateway.'],
  ['Telegram бот на Python', 'Т-Банк', 'T', 'Python разработчик', 'junior', ['Python', 'aiogram', 'SQLite'], 'Бот для трекинга привычек с напоминаниями и статистикой.'],
  ['CI/CD пайплайн', 'Wildberries', 'WB', 'DevOps инженер', 'middle', ['GitLab CI', 'Docker', 'Nginx', 'Ansible'], 'Настроить полный CI/CD пайплайн для Node.js приложения с тестами и деплоем.'],
  ['Нагрузочное тестирование API', 'МТС', '●', 'QA инженер', 'middle', ['JMeter', 'Gatling', 'Python', 'SQL'], 'Разработать план и провести нагрузочное тестирование REST API.']
].map((item, index) => ({ id: index + 1, title: item[0], company: item[1], logo: item[2], role: item[3], level: item[4], tags: item[5], text: item[6] }))

export const skills = [
  ['Go', 95, 2660],
  ['SQL', 65, 1820],
  ['PostgreSQL', 56, 1568],
  ['Docker', 55, 1540],
  ['Git', 48, 1344],
  ['REST API', 41, 1148],
  ['Kafka', 40, 1120],
  ['Linux', 37, 1036],
  ['gRPC', 35, 980]
].map((item, index) => ({ rank: index + 1, name: item[0], percent: item[1], vacancies: item[2] }))

export const professions = ['Backend разработчик', 'C# разработчик', 'Data Scientist', 'DevOps инженер', 'Frontend разработчик', 'Golang разработчик', 'Java разработчик', 'PHP разработчик', 'Python разработчик', 'QA тестировщик', 'Аналитик данных', 'Бизнес-аналитик', 'Продуктовый аналитик', 'Системный аналитик', 'Мобильный разработчик', 'UX/UI дизайнер']
