import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent, type ChangeEvent } from 'react'
import { errText, fetchAll, form, imgUrl, json } from '../api'
import type { Category, Dish } from '../types'

/** Страница меню: блюда (CRUD с фото) и категории (создание, переименование, удаление). */

const categoriesKey = ['categories']
const dishesKey = ['dishes']

export default function Menu() {
  const qc = useQueryClient()
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Dish | null>(null)
  const [creating, setCreating] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [newCategory, setNewCategory] = useState('')
  const [renamingId, setRenamingId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const categories = useQuery({ queryKey: categoriesKey, queryFn: () => fetchAll<Category>('/categories/') })
  const dishes = useQuery({ queryKey: dishesKey, queryFn: () => fetchAll<Dish>('/dishes/', 10) })

  const fail = (e: unknown) => setError(errText(e))
  const clear = () => {
    setError('')
    qc.invalidateQueries({ queryKey: dishesKey })
    qc.invalidateQueries({ queryKey: categoriesKey })
  }

  const createDish = useMutation({
    mutationFn: (data: FormData) => form<Dish>('POST', '/dishes/create/', data),
    onSuccess: () => {
      setCreating(false)
      clear()
    },
    onError: fail,
  })

  const updateDish = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FormData }) =>
      form<Dish>('PATCH', `/dishes/${id}/edit/`, data),
    onSuccess: () => {
      setEditing(null)
      clear()
    },
    onError: fail,
  })

  const deleteDish = useMutation({
    mutationFn: (id: number) => json<never>('DELETE', `/dishes/${id}/edit/`),
    onSuccess: () => {
      setConfirmDelete(null)
      clear()
    },
    onError: (e) => {
      setConfirmDelete(null)
      fail(e)
    },
  })

  const createCategory = useMutation({
    mutationFn: (name: string) => json<Category>('POST', '/categories/create/', { name }),
    onSuccess: () => {
      setNewCategory('')
      clear()
    },
    onError: fail,
  })

  const renameCategory = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      json<Category>('PATCH', `/categories/${id}/edit/`, { name }),
    onSuccess: () => {
      setRenamingId(null)
      clear()
    },
    onError: fail,
  })

  const deleteCategory = useMutation({
    mutationFn: (id: number) => json<never>('DELETE', `/categories/${id}/edit/`),
    onSuccess: clear,
    onError: (e) => {
      setConfirmDelete(null)
      fail(e)
    },
  })

  if (dishes.isLoading || categories.isLoading) return <p>Загружаем меню...</p>
  if (dishes.isError) return <p className="error">Не удалось загрузить меню: {errText(dishes.error)}</p>

  return (
    <div>
      <h2>Меню</h2>
      {error && <p className="hint error">{error}</p>}

      {/* Категории */}
      <div className="panel">
        <strong>Категории</strong>
        <div className="rows">
          {(categories.data ?? []).map((category) => (
            <div className="row" key={category.id}>
              {renamingId === category.id ? (
                <>
                  <input
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                  />
                  <button onClick={() => renameCategory.mutate({ id: category.id, name: renameValue })}>
                    Сохранить
                  </button>
                  <button onClick={() => setRenamingId(null)}>Отмена</button>
                </>
              ) : (
                <>
                  <span>{category.name}</span>
                  <button
                    onClick={() => {
                      setRenamingId(category.id)
                      setRenameValue(category.name)
                    }}
                  >
                    Переименовать
                  </button>
                  <button
                    className="danger"
                    onClick={() =>
                      confirmDelete === category.id
                        ? deleteCategory.mutate(category.id)
                        : setConfirmDelete(category.id)
                    }
                  >
                    {confirmDelete === category.id ? 'Точно удалить?' : 'Удалить'}
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
        <div className="toolbar">
          <input
            placeholder="Новая категория, например Напитки"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
          />
          <button
            className="primary"
            disabled={!newCategory.trim()}
            onClick={() => createCategory.mutate(newCategory.trim())}
          >
            Добавить категорию
          </button>
        </div>
      </div>

      {/* Блюда */}
      <div className="toolbar">
        <button className="primary" onClick={() => { setCreating(true); setEditing(null) }}>
          Добавить блюдо
        </button>
      </div>

      {(creating || editing) && (
        <>
          <DishForm
            key={editing ? `edit-${editing.id}` : 'create'}
            dish={editing}
            categories={categories.data ?? []}
            busy={createDish.isPending || updateDish.isPending}
            onCancel={() => {
              setCreating(false)
              setEditing(null)
            }}
            onSubmit={(data, fileChanged) => {
              if (editing) {
                if (!fileChanged) data.delete('image')
                updateDish.mutate({ id: editing.id, data })
              } else {
                createDish.mutate(data)
              }
            }}
          />
        </>
      )}

      <table>
        <thead>
          <tr>
            <th>Фото</th>
            <th>Название</th>
            <th>Категория</th>
            <th>Цена</th>
            <th>Состав</th>
            <th>Доступно</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {(dishes.data ?? []).map((dish) => (
            <tr key={dish.id} data-dish-id={dish.id}>
              <td>
                {dish.image ? (
                  <img className="thumb" src={imgUrl(dish.image) ?? ''} alt={dish.name} />
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>
                {dish.name}
                {dish.description && <div className="muted small">{dish.description}</div>}
              </td>
              <td>{dish.category?.name ?? '—'}</td>
              <td>{dish.price}</td>
              <td className="small">{dish.ingredients || '—'}</td>
              <td>
                <span className={`badge ${dish.is_available ? 'ok' : 'bad'}`}>
                  {dish.is_available ? 'Да' : 'Нет'}
                </span>
              </td>
              <td>
                <button onClick={() => { setEditing(dish); setCreating(false) }}>Изменить</button>
                <button
                  className="danger"
                  disabled={deleteDish.isPending}
                  onClick={() =>
                    confirmDelete === dish.id
                      ? deleteDish.mutate(dish.id)
                      : setConfirmDelete(dish.id)
                  }
                >
                  {confirmDelete === dish.id ? 'Точно удалить?' : 'Удалить'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

type DishFormProps = {
  dish: Dish | null
  categories: Category[]
  busy: boolean
  onCancel: () => void
  onSubmit: (data: FormData, fileChanged: boolean) => void
}

function DishForm({ dish, categories, busy, onCancel, onSubmit }: DishFormProps) {
  const [name, setName] = useState(dish?.name ?? '')
  const [description, setDescription] = useState(dish?.description ?? '')
  const [ingredients, setIngredients] = useState(dish?.ingredients ?? '')
  const [price, setPrice] = useState(dish?.price ?? '')
  const [categoryId, setCategoryId] = useState(String(dish?.category?.id ?? ''))
  const [isAvailable, setIsAvailable] = useState(dish?.is_available ?? true)
  const [file, setFile] = useState<File | null>(null)
  const [localError, setLocalError] = useState('')
  const [preview, setPreview] = useState<string | null>(imgUrl(dish?.image))

  function pickFile(event: ChangeEvent<HTMLInputElement>) {
    const picked = event.target.files?.[0] ?? null
    setFile(picked)
    setPreview(picked ? URL.createObjectURL(picked) : imgUrl(dish?.image))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    setLocalError('')
    if (!name.trim() || !price || !categoryId) {
      setLocalError('Заполните название, цену и категорию')
      return
    }
    const data = new FormData()
    data.set('name', name.trim())
    data.set('description', description)
    data.set('ingredients', ingredients)
    data.set('price', price)
    data.set('category_id', categoryId)
    data.set('is_available', isAvailable ? 'true' : 'false')
    if (file) data.set('image', file)
    onSubmit(data, Boolean(file))
  }

  return (
    <div className="panel" data-testid="dish-form">
      <strong>{dish ? `Изменяем: ${dish.name}` : 'Новое блюдо'}</strong>
      <div className="row">
        <div>
          <label>Название</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label>Цена</label>
          <input value={price} onChange={(e) => setPrice(e.target.value)} placeholder="490.00" />
        </div>
        <div>
          <label>Категория</label>
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            <option value="">— выбери —</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div>
        <label>Состав (через запятую)</label>
        <input value={ingredients} onChange={(e) => setIngredients(e.target.value)} />
      </div>
      <div>
        <label>Описание</label>
        <input value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div className="row">
        <div>
          <label>Фото</label>
          <input type="file" accept="image/*" onChange={pickFile} />
        </div>
        {preview && <img className="thumb" src={preview} alt="Превью" />}
        <label className="check">
          <input
            type="checkbox"
            checked={isAvailable}
            onChange={(e) => setIsAvailable(e.target.checked)}
          />
          Доступно сейчас
        </label>
      </div>
      {localError && <p className="hint error">{localError}</p>}
      <div className="toolbar">
        <button className="primary" disabled={busy} onClick={submit}>
          Сохранить
        </button>
        <button onClick={onCancel}>Отмена</button>
      </div>
    </div>
  )
}
