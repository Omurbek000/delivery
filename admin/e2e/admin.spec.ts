/** E2E-проверка всей админ-панели: логин, заказы, меню, акции, юзеры, дэшборд. */

import { expect, test, type APIRequestContext } from '@playwright/test'

const BACKEND = 'http://localhost:8000'
const ADMIN = { phone: '+996777666555', password: 'AdminPanel2026!' }
const CLIENT = { phone: '+996555999001', password: 'StroNG-Secret2026' }

/** Возвращает заголовок Authorization для прямых запросов к API. */
async function auth(request: APIRequestContext): Promise<string> {
  const res = await request.post(`${BACKEND}/login/`, { data: ADMIN })
  const data = await res.json()
  return `Bearer ${data.access as string}`
}

test('полный проход по панели', async ({ page, request }) => {
  // --- Подготовка через API: тестовый клиент и заказ для смены статуса ---
  const bearer = await auth(request)
  await request.post(`${BACKEND}/register/`, { data: CLIENT })

  // Убираем мусор от прошлого запуска (если тест падал посреди)
  const codesRes = await request.get(`${BACKEND}/promo-codes/`, {
    headers: { Authorization: bearer },
  })
  const codes = (await codesRes.json()) as { results?: { code: string; id: number }[] }
  for (const leftover of codes.results ?? []) {
    if (leftover.code === 'E2E10') {
      await request.delete(`${BACKEND}/promo-codes/${leftover.id}/edit/`, {
        headers: { Authorization: bearer },
      })
    }
  }

  const dishesRes = await request.get(`${BACKEND}/dishes/`)
  const dishes = (await dishesRes.json()) as { results: { id: number; name: string }[] }
  expect(dishes.results.length).toBeGreaterThan(0)
  const firstDish = dishes.results[0]

  const orderRes = await request.post(`${BACKEND}/orders/create/`, {
    headers: { Authorization: bearer },
    data: {
      street: 'Абдрахманова',
      house: '5',
      items: [{ dish_id: firstDish.id, quantity: 1 }],
      comment: 'e2e',
    },
  })
  expect(orderRes.ok()).toBeTruthy()
  const created = (await orderRes.json()) as { id: number }

  // --- Логин ---
  await page.goto('/login')
  await page.getByPlaceholder('+996...').fill(ADMIN.phone)
  await page.getByPlaceholder('Пароль').fill(ADMIN.password)
  await page.getByRole('button', { name: 'Войти' }).click()
  await expect(page).toHaveURL('/orders')

  // --- Заказы: строка видна, статус переводим по матрице created → confirmed ---
  const row = page.locator(`tr[data-order-id="${created.id}"]`)
  await expect(row).toContainText('Создан')
  await row.getByRole('button', { name: 'Подтверждён' }).click()
  await expect(row).toContainText('Подтверждён')
  await expect(row.getByRole('button', { name: 'Готовится' })).toBeVisible()

  // --- Меню: категории создаются, переименовываются, удаляются ---
  await page.getByRole('link', { name: 'Меню' }).click()
  await expect(page.getByRole('heading', { name: 'Меню' })).toBeVisible()
  await expect(page.locator(`tr[data-dish-id="${firstDish.id}"]`)).toContainText(firstDish.name)

  await page.getByPlaceholder('Новая категория, например Напитки').fill('E2E категория')
  await page.getByRole('button', { name: 'Добавить категорию' }).click()
  const catRow = page.locator('.panel .row').filter({ hasText: 'E2E категория' })
  await expect(catRow).toBeVisible()

  await catRow.getByRole('button', { name: 'Переименовать' }).click()
  // В режиме переименования есть только одна строка с input
  const renamingRow = page.locator('.panel .row').filter({ has: page.locator('input') })
  await renamingRow.locator('input').fill('E2E категория 2')
  await renamingRow.getByRole('button', { name: 'Сохранить' }).click()
  const renamedRow = page.locator('.panel .row').filter({ hasText: 'E2E категория 2' })
  await expect(renamedRow).toBeVisible()
  await renamedRow.getByRole('button', { name: 'Удалить' }).click()
  await renamedRow.getByRole('button', { name: 'Точно удалить?' }).click()
  await expect(page.locator('.panel .row').filter({ hasText: 'E2E категория 2' })).toHaveCount(0)

  // --- Меню: блюдо создаётся и удаляется ---
  await page.getByRole('button', { name: 'Добавить блюдо' }).click()
  const form = page.getByTestId('dish-form')
  await form.locator('input').first().fill('E2E ролл')
  await form.getByPlaceholder('490.00').fill('777.00')
  const catValue = await form.locator('select option').nth(1).getAttribute('value')
  await form.locator('select').selectOption(catValue ?? '')
  await form.locator('input[type="checkbox"]').check()
  await form.getByRole('button', { name: 'Сохранить' }).click()
  const dishRow = page.locator('tr').filter({ hasText: 'E2E ролл' })
  await expect(dishRow).toContainText('777.00')
  await dishRow.getByRole('button', { name: 'Удалить' }).click()
  await dishRow.getByRole('button', { name: 'Точно удалить?' }).click()
  await expect(page.locator('tr').filter({ hasText: 'E2E ролл' })).toHaveCount(0)

  // --- Акции и промокоды ---
  await page.getByRole('link', { name: 'Акции и промокоды' }).click()
  await expect(
    page.getByRole('heading', { name: 'Промокоды', exact: true }),
  ).toBeVisible()

  // Промокод: создаём, отключаем, удаляем
  const codePanel = page.locator('.panel').filter({ hasText: 'Новый промокод' })
  await codePanel.getByPlaceholder('Доставка15').fill('E2E10')
  await codePanel.locator('input').nth(1).fill('10')
  await codePanel.getByRole('button', { name: 'Создать промокод' }).click()
  const codeRow = page.locator('tr[data-code="E2E10"]')
  await expect(codeRow).toContainText('10.00%')
  await codeRow.getByRole('button', { name: 'Отключить' }).click()
  await expect(codeRow).toContainText('Нет')
  await codeRow.getByRole('button', { name: 'Удалить' }).click()
  await expect(page.locator('tr[data-code="E2E10"]')).toHaveCount(0)

  // Акция: создаём (новая цена 500 · 0.8 = 400) и удаляем
  const promoPanel = page.locator('.panel').filter({ hasText: 'Новая акция' })
  await promoPanel.locator('input').nth(0).fill('Счастливый час')
  await promoPanel.locator('input').nth(1).fill('500.00')
  await promoPanel.locator('input').nth(2).fill('20')
  await promoPanel.locator('select').selectOption(String(firstDish.id))
  await promoPanel.locator('input').nth(3).fill('7')
  await promoPanel.getByRole('button', { name: 'Создать акцию' }).click()
  const promoRow = page.locator('tr').filter({ hasText: 'Счастливый час' })
  await expect(promoRow).toContainText('400.00')
  await promoRow.getByRole('button', { name: 'Удалить' }).click()
  await expect(page.locator('tr').filter({ hasText: 'Счастливый час' })).toHaveCount(0)

  // --- Пользователи: бан и разбан тестового клиента ---
  await page.getByRole('link', { name: 'Пользователи' }).click()
  const userRow = page.locator('tr').filter({ hasText: CLIENT.phone })
  await expect(userRow).toContainText('активен')
  await userRow.getByRole('button', { name: 'Забанить' }).click()
  await expect(userRow).toContainText('забанен')
  await userRow.getByRole('button', { name: 'Разбанить' }).click()
  await expect(userRow).toContainText('активен')

  // --- Дэшборд: числа на месте ---
  await page.getByRole('link', { name: 'Дэшборд' }).click()
  await expect(page.getByText('Заказов сегодня')).toBeVisible()
  await expect(page.locator('.cards .card .num').first()).not.toHaveText('0')
  await expect(page.getByText('Выручка за сегодня')).toBeVisible()
  await expect(page.locator('tr').filter({ hasText: 'Подтверждён' })).toBeVisible()

  // --- Выход ---
  await page.getByRole('button', { name: 'Выйти' }).click()
  await expect(page).toHaveURL('/login')
})

test('собранная панель отдаётся Django по /panel/', async ({ request }) => {
  const res = await request.get(`${BACKEND}/panel/`)
  expect(res.ok()).toBeTruthy()
  const html = await res.text()
  expect(html).toContain('Панель Онигири')
  const match = /<script[^>]+src="([^"]+)"/.exec(html)
  expect(match).toBeTruthy()
  const js = await request.get(`${BACKEND}${match![1] as string}`)
  await expect(js).toBeOK()
})

test('вход в панель работает через /panel/ в проде', async ({ page }) => {
  await page.goto(`${BACKEND}/panel/login`)
  await page.getByPlaceholder('+996...').fill(ADMIN.phone)
  await page.getByPlaceholder('Пароль').fill(ADMIN.password)
  await page.getByRole('button', { name: 'Войти' }).click()
  await expect(page).toHaveURL(`${BACKEND}/panel/orders`)
})
