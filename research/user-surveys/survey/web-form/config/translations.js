const en = {
  title: 'UA Passport Slot Monitor survey', language: 'Language', intro: { heading: 'Help improve the queue experience', body: 'This voluntary research survey takes about 3-5 minutes.' },
  debug: { heading: 'Developer demo payload', help: 'Visible only when the page is opened with debug=1. This payload is not saved or sent.', responseId: 'Response ID' },
  privacyNotice: 'Please do not include names, contact details, passport data, appointment numbers, or exact addresses.',
  notOfficial: 'This is an independent research form, not the official DP “Dokument” website. Submitting it does not book an appointment, create a subscription, or guarantee availability.',
  sections: { introduction: 'Introduction', situation: 'Your situation', centres: 'Service centres', problems: 'Problems and product interaction', notifications: 'Notifications and CAPTCHA', testing: 'Testing and final context' },
  questions: {
    research_consent: { title: 'I agree that my anonymous answers may be used for this research.', help: 'This consent is required. Do not include personal information.', required: 'Please provide research consent.' },
    residence_region: { title: 'Where do you currently live?', options: { eu: 'European Union', united_kingdom: 'United Kingdom', canada: 'Canada', other_country: 'Another country' } },
    document_service: { title: 'Which service do you need?', options: { international_passport: 'International passport', id_card: 'ID card', passport_exchange: 'Passport exchange', id_and_passport: 'ID card and international passport', other: 'Other' } },
    other_service_text: { title: 'Describe the other service', help: 'Service type only, not document or appointment details.' },
    slot_search_experience: { title: 'What best describes your queue experience?', options: { not_started: 'I have not started searching', searching_now: 'I am searching now', searched_before: 'I searched before', booked_before: 'I booked before' } },
    check_frequency: { title: 'How often do you check for available slots?', options: { several_times_daily: 'Several times a day', daily: 'Daily', several_times_weekly: 'Several times a week', occasionally: 'Occasionally', not_checking_yet: 'I am not checking yet' } },
    search_duration: { title: 'How long have you been searching?', options: { under_1_week: 'Less than 1 week', one_to_4_weeks: '1-4 weeks', one_to_3_months: '1-3 months', over_3_months: 'More than 3 months', not_sure: 'Not sure' } },
    appointment_urgency: { title: 'When would you ideally need an appointment?', options: { within_2_weeks: 'Within 2 weeks', within_1_month: 'Within 1 month', within_3_months: 'Within 3 months', later: 'Later', not_sure: 'Not sure' } },
    desired_centres: { title: 'Which service centres would you consider?', help: 'Select 1-5 centres. Availability is not implied.' },
    other_centre_text: { title: 'Name the other centre', help: 'Centre name only, not an address or appointment detail.' },
    problem_categories: { title: 'What problems have you experienced?', help: 'Choose up to 5.' },
    other_problem_text: { title: 'Describe the other problem', help: 'Do not include personal or document information.' },
    cross_border_flexibility: { title: 'Would you consider a centre in another country?', options: { yes: 'Yes', maybe: 'Maybe', no: 'No', not_sure: 'Not sure' } },
    notification_channels: { title: 'Which notification channels would you prefer?', help: 'Preference only. This does not create a subscription. Choose up to 3.' },
    other_notification_channel_text: { title: 'Name the other channel', help: 'Channel type only. Do not enter an email, phone number, or username.' },
    primary_notification_channel: { title: 'Which would be your primary channel?' },
    manual_captcha_attitude: { title: 'How would you feel about occasional manual CAPTCHA hand-off?', help: 'This records a product preference and does not authorize CAPTCHA bypass.', options: { acceptable: 'Acceptable', acceptable_if_rare: 'Acceptable if rare', require_full_automation: 'I require full automation', not_sure: 'Not sure' } },
    early_testing_interest: { title: 'Would you be interested in early testing?', help: 'This does not collect contact details.', options: { yes: 'Yes', no: 'No', maybe: 'Maybe' } },
    additional_context: { title: 'Anything else to share?', help: 'Optional. Maximum 500 characters. Do not include personal, document, contact, or appointment information.' },
  },
  controls: { required: 'Required', optional: 'Optional', back: 'Back', next: 'Continue', submit: 'Submit survey', loading: 'Loading survey...', submitting: 'Submitting...', success: 'Thank you. Your anonymous research response was accepted.', demoSuccess: 'Demo mode: your response was validated locally and was not sent to a server.', error: 'We could not confirm submission. Your answers are still here. Please try again.', retry: 'Retry', taxonomyError: 'The survey options could not be loaded. Please reload the page.', invalid: 'Please review the highlighted fields.', max: 'Please select no more than {count}.', length: 'Please keep this answer within {count} characters.' },
};

const uk = structuredClone(en);
const ru = structuredClone(en);
Object.assign(uk, { title: 'Опитування UA Passport Slot Monitor', language: 'Мова', privacyNotice: 'Не вказуйте імена, контактні дані, паспортні дані, номери запису або точні адреси.', notOfficial: 'Це незалежна дослідницька форма, а не офіційний сайт ДП «Документ». Надсилання не записує на прийом, не створює підписку і не гарантує доступність.' });
Object.assign(ru, { title: 'Опрос UA Passport Slot Monitor', language: 'Язык', privacyNotice: 'Не указывайте имена, контактные данные, паспортные данные, номера записи или точные адреса.', notOfficial: 'Это независимая исследовательская форма, а не официальный сайт ДП «Документ». Отправка не записывает на приём, не создаёт подписку и не гарантирует доступность.' });
uk.debug = { heading: 'Payload демо-режиму', help: 'Видно лише коли сторінку відкрито з параметром debug=1. Payload не зберігається і не надсилається.', responseId: 'ID відповіді' };
ru.debug = { heading: 'Payload демо-режима', help: 'Видно только если страница открыта с параметром debug=1. Payload не сохраняется и не отправляется.', responseId: 'ID ответа' };
uk.intro = { heading: 'Допоможіть покращити роботу черги', body: 'Це добровільне дослідження, яке займає близько 3-5 хвилин.' };
ru.intro = { heading: 'Помогите улучшить работу очереди', body: 'Это добровольное исследование, которое занимает около 3-5 минут.' };

const localized = {
  uk: {
    sections: ['Вступ', 'Ваша ситуація', 'Сервісні центри', 'Проблеми та взаємодія з продуктом', 'Сповіщення та CAPTCHA', 'Тестування та додатковий контекст'],
    titles: ['Я погоджуюся, що мої анонімні відповіді можуть використовуватися для цього дослідження.', 'Де ви зараз живете?', 'Яка послуга вам потрібна?', 'Опишіть іншу послугу', 'Що найкраще описує ваш досвід із чергою?', 'Як часто ви перевіряєте доступні слоти?', 'Як довго ви шукаєте?', 'Коли вам бажано отримати запис?', 'Які сервісні центри ви розглядаєте?', 'Назвіть інший центр', 'З якими проблемами ви стикалися?', 'Опишіть іншу проблему', 'Чи розглянули б ви центр в іншій країні?', 'Які канали сповіщень ви хотіли б використовувати?', 'Назвіть інший канал', 'Який канал був би для вас основним?', 'Як ви ставитеся до періодичної ручної передачі CAPTCHA?', 'Чи цікаве вам раннє тестування?', 'Що ще ви хотіли б повідомити?'],
    options: { eu: 'Європейський Союз', united_kingdom: 'Велика Британія', canada: 'Канада', other_country: 'Інша країна', international_passport: 'Закордонний паспорт', id_card: 'ID-картка', passport_exchange: 'Обмін паспорта', id_and_passport: 'ID-картка та закордонний паспорт', other: 'Інше', not_started: 'Ще не починав(-ла) пошук', searching_now: 'Шукаю зараз', searched_before: 'Шукав(-ла) раніше', booked_before: 'Раніше записувався(-лася)', several_times_daily: 'Кілька разів на день', daily: 'Щодня', several_times_weekly: 'Кілька разів на тиждень', occasionally: 'Час від часу', not_checking_yet: 'Ще не перевіряю', under_1_week: 'Менше тижня', one_to_4_weeks: '1-4 тижні', one_to_3_months: '1-3 місяці', over_3_months: 'Понад 3 місяці', not_sure: 'Не знаю', within_2_weeks: 'Протягом 2 тижнів', within_1_month: 'Протягом місяця', within_3_months: 'Протягом 3 місяців', later: 'Пізніше', yes: 'Так', maybe: 'Можливо', no: 'Ні', acceptable: 'Прийнятно', acceptable_if_rare: 'Прийнятно, якщо це рідко', require_full_automation: 'Потрібна повна автоматизація' }
  },
  ru: {
    sections: ['Введение', 'Ваша ситуация', 'Сервисные центры', 'Проблемы и взаимодействие с продуктом', 'Уведомления и CAPTCHA', 'Тестирование и дополнительный контекст'],
    titles: ['Я согласен(на), что мои анонимные ответы могут использоваться для этого исследования.', 'Где вы сейчас живёте?', 'Какая услуга вам нужна?', 'Опишите другую услугу', 'Что лучше всего описывает ваш опыт с очередью?', 'Как часто вы проверяете доступные слоты?', 'Как долго вы ищете?', 'Когда вам желательно получить запись?', 'Какие сервисные центры вы рассматриваете?', 'Назовите другой центр', 'С какими проблемами вы сталкивались?', 'Опишите другую проблему', 'Рассмотрели бы вы центр в другой стране?', 'Какие каналы уведомлений вы хотели бы использовать?', 'Назовите другой канал', 'Какой канал был бы для вас основным?', 'Как вы относитесь к периодической ручной передаче CAPTCHA?', 'Интересно ли вам раннее тестирование?', 'Что ещё вы хотели бы сообщить?'],
    options: { eu: 'Европейский Союз', united_kingdom: 'Великобритания', canada: 'Канада', other_country: 'Другая страна', international_passport: 'Заграничный паспорт', id_card: 'ID-карта', passport_exchange: 'Обмен паспорта', id_and_passport: 'ID-карта и заграничный паспорт', other: 'Другое', not_started: 'Ещё не начинал(а) поиск', searching_now: 'Ищу сейчас', searched_before: 'Искал(а) раньше', booked_before: 'Раньше записывался(лась)', several_times_daily: 'Несколько раз в день', daily: 'Ежедневно', several_times_weekly: 'Несколько раз в неделю', occasionally: 'Время от времени', not_checking_yet: 'Пока не проверяю', under_1_week: 'Меньше недели', one_to_4_weeks: '1-4 недели', one_to_3_months: '1-3 месяца', over_3_months: 'Больше 3 месяцев', within_2_weeks: 'В течение 2 недель', within_1_month: 'В течение месяца', within_3_months: 'В течение 3 месяцев', later: 'Позже', yes: 'Да', maybe: 'Возможно', no: 'Нет', acceptable: 'Приемлемо', acceptable_if_rare: 'Приемлемо, если редко', require_full_automation: 'Требую полной автоматизации' }
  }
};

for (const target of [uk, ru]) {
  target.controls = { ...en.controls, required: target === uk ? 'Обов’язкове' : 'Обязательно', optional: target === uk ? 'Необов’язково' : 'Необязательно', back: 'Назад', next: target === uk ? 'Продовжити' : 'Продолжить', submit: target === uk ? 'Надіслати опитування' : 'Отправить опрос', submitting: target === uk ? 'Надсилання...' : 'Отправка...', success: target === uk ? 'Дякуємо. Анонімну відповідь прийнято.' : 'Спасибо. Анонимный ответ принят.', demoSuccess: target === uk ? 'Демо-режим: відповідь перевірено локально, на сервер її не надсилали.' : 'Демо-режим: ответ проверен локально и не отправлялся на сервер.', invalid: target === uk ? 'Перевірте виділені поля.' : 'Проверьте выделенные поля.', taxonomyError: target === uk ? 'Не вдалося завантажити варіанти опитування. Перезавантажте сторінку.' : 'Не удалось загрузить варианты опроса. Перезагрузите страницу.', error: target === uk ? 'Не вдалося підтвердити надсилання. Відповіді збережено на цій сторінці.' : 'Не удалось подтвердить отправку. Ответы остались на этой странице.' };
}

for (const [locale, values] of Object.entries(localized)) {
  values.sections.forEach((value, index) => { Object.assign(locale === 'uk' ? uk : ru, { sections: { ...(locale === 'uk' ? uk.sections : ru.sections), [Object.keys(en.sections)[index]]: value } }); });
  questionsForTranslation(values, locale === 'uk' ? uk : ru);
}

function questionsForTranslation(values, target) {
  const ids = ['research_consent', 'residence_region', 'document_service', 'other_service_text', 'slot_search_experience', 'check_frequency', 'search_duration', 'appointment_urgency', 'desired_centres', 'other_centre_text', 'problem_categories', 'other_problem_text', 'cross_border_flexibility', 'notification_channels', 'other_notification_channel_text', 'primary_notification_channel', 'manual_captcha_attitude', 'early_testing_interest', 'additional_context'];
  ids.forEach((id, index) => { target.questions[id].title = values.titles[index]; });
  for (const question of Object.values(target.questions)) if (question.options) for (const id of Object.keys(question.options)) question.options[id] = values.options[id] || question.options[id];
}

const sharedLabels = {
  uk: { not_sure: 'Не впевнений(-а)', other: 'Інше', other_centre: 'Інший центр', not_decided: 'Ще не визначився(-лася)', none: 'Нічого з переліченого', telegram: 'Telegram', whatsapp: 'WhatsApp', email: 'Електронна пошта', sms: 'SMS', browser_push: 'Push-повідомлення у браузері', mobile_app: 'Окремий мобільний застосунок' },
  ru: { not_sure: 'Не уверен(а)', other: 'Другое', other_centre: 'Другой центр', not_decided: 'Ещё не определился(лась)', none: 'Ничего из перечисленного', telegram: 'Telegram', whatsapp: 'WhatsApp', email: 'Электронная почта', sms: 'SMS', browser_push: 'Push-уведомления в браузере', mobile_app: 'Отдельное мобильное приложение' },
};
const helpText = {
  uk: { research_consent: 'Ця згода обов’язкова. Не вказуйте персональну інформацію.', search_duration: '', desired_centres: 'Виберіть 1-5 центрів. Доступність не мається на увазі.', other_centre_text: 'Лише назва центру, без адреси чи деталей запису.', problem_categories: 'Виберіть до 5 варіантів.', other_problem_text: 'Не вказуйте персональну або документальну інформацію.', notification_channels: 'Це лише побажання. Підписка не створюється. Виберіть до 3 варіантів.', other_notification_channel_text: 'Лише тип каналу. Не вводьте електронну пошту, номер телефону або ім’я користувача.', manual_captcha_attitude: 'Це лише побажання щодо продукту і не дозволяє обходити CAPTCHA.', early_testing_interest: 'Контактні дані не збираються.', additional_context: 'Необов’язково. Максимум 500 символів. Не вказуйте персональні, документальні, контактні дані або дані запису.' },
  ru: { research_consent: 'Это согласие обязательно. Не указывайте персональную информацию.', desired_centres: 'Выберите 1-5 центров. Доступность не подразумевается.', other_centre_text: 'Только название центра, без адреса или деталей записи.', problem_categories: 'Выберите до 5 вариантов.', other_problem_text: 'Не указывайте персональную или документальную информацию.', notification_channels: 'Это только предпочтение. Подписка не создаётся. Выберите до 3 вариантов.', other_notification_channel_text: 'Только тип канала. Не вводите электронную почту, номер телефона или имя пользователя.', manual_captcha_attitude: 'Это только предпочтение по продукту и не разрешает обход CAPTCHA.', early_testing_interest: 'Контактные данные не собираются.', additional_context: 'Необязательно. Максимум 500 символов. Не указывайте персональные, документальные, контактные данные или данные записи.' },
};
for (const locale of ['uk', 'ru']) {
  const target = locale === 'uk' ? uk : ru;
  for (const question of Object.values(target.questions)) {
    for (const [id, label] of Object.entries(sharedLabels[locale])) if (question.options?.[id]) question.options[id] = label;
    if (helpText[locale][question.id]) question.help = helpText[locale][question.id];
  }
}

const completeLocalizedText = {
  uk: {
    questions: {
      research_consent: { help: 'Ця згода обов’язкова. Не вказуйте персональну інформацію.', required: 'Надайте згоду на дослідження.' },
      residence_region: { help: 'Оберіть регіон проживання без указання точної адреси.' },
      document_service: { help: 'Оберіть потрібну послугу.' },
      other_service_text: { help: 'Лише тип послуги, без даних документа або запису.' },
      slot_search_experience: { help: 'Оберіть варіант, який найкраще описує ваш досвід.' },
      check_frequency: { help: 'Вкажіть приблизну частоту перевірок.' },
      search_duration: { help: 'Оберіть приблизний період пошуку.' },
      appointment_urgency: { help: 'Оберіть бажаний термін без указання причини.' },
      desired_centres: { help: 'Виберіть 1-5 центрів. Доступність не мається на увазі.' },
      other_centre_text: { help: 'Лише назва центру, без адреси чи деталей запису.' },
      problem_categories: { help: 'Виберіть до 5 варіантів.' },
      other_problem_text: { help: 'Не вказуйте персональну або документальну інформацію.' },
      notification_channels: { help: 'Це лише побажання. Підписка не створюється. Виберіть до 3 варіантів.' },
      other_notification_channel_text: { help: 'Лише тип каналу. Не вводьте електронну пошту, номер телефону або ім’я користувача.' },
      cross_border_flexibility: { help: 'Враховуйте лише загальну готовність розглядати іншу країну.' },
      primary_notification_channel: { help: 'Оберіть один із вибраних каналів.' },
      manual_captcha_attitude: { help: 'Це лише побажання щодо продукту і не дозволяє обходити CAPTCHA.' },
      early_testing_interest: { help: 'Контактні дані не збираються.' },
      additional_context: { help: 'Необов’язково. Максимум 500 символів. Не вказуйте персональні, документальні, контактні дані або дані запису.' },
    },
    controls: { loading: 'Завантаження опитування...', retry: 'Повторити', max: 'Виберіть не більше {count} варіантів.', length: 'Обмежте відповідь до {count} символів.' },
  },
  ru: {
    questions: {
      research_consent: { help: 'Это согласие обязательно. Не указывайте персональную информацию.', required: 'Предоставьте согласие на исследование.' },
      residence_region: { help: 'Выберите регион проживания без указания точного адреса.' },
      document_service: { help: 'Выберите нужную услугу.' },
      other_service_text: { help: 'Только тип услуги, без данных документа или записи.' },
      slot_search_experience: { help: 'Выберите вариант, который лучше всего описывает ваш опыт.' },
      check_frequency: { help: 'Укажите примерную частоту проверок.' },
      search_duration: { help: 'Выберите примерный период поиска.' },
      appointment_urgency: { help: 'Выберите желаемый срок без указания причины.' },
      desired_centres: { help: 'Выберите 1-5 центров. Доступность не подразумевается.' },
      other_centre_text: { help: 'Только название центра, без адреса или деталей записи.' },
      problem_categories: { help: 'Выберите до 5 вариантов.' },
      other_problem_text: { help: 'Не указывайте персональную или документальную информацию.' },
      notification_channels: { help: 'Это только предпочтение. Подписка не создаётся. Выберите до 3 вариантов.' },
      other_notification_channel_text: { help: 'Только тип канала. Не вводите электронную почту, номер телефона или имя пользователя.' },
      cross_border_flexibility: { help: 'Учитывайте только общую готовность рассматривать другую страну.' },
      primary_notification_channel: { help: 'Выберите один из отмеченных каналов.' },
      manual_captcha_attitude: { help: 'Это только предпочтение по продукту и не разрешает обход CAPTCHA.' },
      early_testing_interest: { help: 'Контактные данные не собираются.' },
      additional_context: { help: 'Необязательно. Максимум 500 символов. Не указывайте персональные, документальные, контактные данные или данные записи.' },
    },
    controls: { loading: 'Загрузка опроса...', retry: 'Повторить', max: 'Выберите не более {count} вариантов.', length: 'Ограничьте ответ до {count} символов.' },
  },
};
for (const locale of ['uk', 'ru']) {
  const target = locale === 'uk' ? uk : ru;
  Object.assign(target.controls, completeLocalizedText[locale].controls);
  for (const [id, values] of Object.entries(completeLocalizedText[locale].questions)) Object.assign(target.questions[id], values);
}

export const translations = Object.freeze({ uk: Object.freeze(uk), ru: Object.freeze(ru), en: Object.freeze(en) });
