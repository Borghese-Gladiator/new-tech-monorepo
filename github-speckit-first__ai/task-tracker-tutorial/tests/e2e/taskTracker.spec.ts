import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
})

test('full user flow: create, complete, filter, persist', async ({ page }) => {
  // Create a task
  await page.getByPlaceholder('What needs to be done?').fill('Buy groceries')
  await page.getByRole('button', { name: 'Add' }).click()
  await expect(page.getByText('Buy groceries')).toBeVisible()

  // Create a second task
  await page.getByPlaceholder('What needs to be done?').fill('Walk the dog')
  await page.getByRole('button', { name: 'Add' }).click()
  await expect(page.getByText('Walk the dog')).toBeVisible()

  // Mark first task complete
  await page.getByRole('checkbox', { name: /Buy groceries/ }).check()
  await expect(page.getByRole('checkbox', { name: /Buy groceries/ })).toBeChecked()

  // Filter to Active — completed task should be hidden
  await page.getByRole('button', { name: 'Active' }).click()
  await expect(page.getByText('Buy groceries')).not.toBeVisible()
  await expect(page.getByText('Walk the dog')).toBeVisible()

  // Filter to Completed — only completed task visible
  await page.getByRole('button', { name: 'Completed' }).click()
  await expect(page.getByText('Buy groceries')).toBeVisible()
  await expect(page.getByText('Walk the dog')).not.toBeVisible()

  // Filter to All — both visible
  await page.getByRole('button', { name: 'All' }).click()
  await expect(page.getByText('Buy groceries')).toBeVisible()
  await expect(page.getByText('Walk the dog')).toBeVisible()

  // Refresh and verify persistence
  await page.reload()
  await expect(page.getByText('Buy groceries')).toBeVisible()
  await expect(page.getByText('Walk the dog')).toBeVisible()
  await expect(page.getByRole('checkbox', { name: /Buy groceries/ })).toBeChecked()
  await expect(page.getByRole('checkbox', { name: /Walk the dog/ })).not.toBeChecked()
})

test('rejects empty task title', async ({ page }) => {
  await page.getByRole('button', { name: 'Add' }).click()
  await expect(page.getByText('Please enter a task title')).toBeVisible()
})

test('edit task title', async ({ page }) => {
  // Create a task
  await page.getByPlaceholder('What needs to be done?').fill('Buy groceries')
  await page.getByRole('button', { name: 'Add' }).click()

  // Edit it
  await page.getByRole('button', { name: /Edit "Buy groceries"/ }).click()
  const editInput = page.getByRole('textbox', { name: /Edit title/ })
  await editInput.clear()
  await editInput.fill('Buy organic groceries')
  await editInput.press('Enter')
  await expect(page.getByText('Buy organic groceries')).toBeVisible()
})

test('delete task with toast', async ({ page }) => {
  // Create a task
  await page.getByPlaceholder('What needs to be done?').fill('Buy groceries')
  await page.getByRole('button', { name: 'Add' }).click()

  // Delete it — check toast immediately after click (before auto-dismiss)
  await page.getByRole('button', { name: /Delete "Buy groceries"/ }).click()
  await expect(page.getByRole('status')).toHaveText('"Buy groceries" deleted')
  await expect(page.locator('.task-item')).toHaveCount(0)
})
