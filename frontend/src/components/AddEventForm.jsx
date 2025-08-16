import { useState } from 'react'
import { parseText, createEvent } from '../services/api'

export default function AddEventForm({ onSaved }) {
  const [text, setText] = useState('')
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [savedMsg, setSavedMsg] = useState('')

  const handleParse = async (e) => {
    e.preventDefault()
    setError('')
    setSavedMsg('')
    setPreview(null)

    if (!text.trim()) return

    try {
      setLoading(true)
      const data = await parseText(text)
      setPreview(data)
    } catch (err) {
      console.error(err)
      setError('Не успях да разбера текста. Опитай да преформулираш.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!preview) return
    try {
      setLoading(true)
      await createEvent({
        title: preview.title,
        start: preview.start,
        end: preview.end,
        raw_text: text,
      })
      setSavedMsg('Събитието е записано!')
      setText('')
      setPreview(null)
      onSaved?.()
    } catch (err) {
      console.error(err)
      setError('Грешка при запис на събитието.')
    } finally {
      setLoading(false)
    }
  }

  const formatDT = (iso) => new Date(iso).toLocaleString('bg-BG', {
    dateStyle: 'medium', timeStyle: 'short'
  })

  return (
    <div className="rounded-2xl bg-white p-4 shadow">
      <h2 className="text-lg font-semibold mb-3">Добави събитие</h2>
      <form onSubmit={handleParse} className="space-y-3">
        <textarea
          className="w-full rounded-xl border border-slate-200 p-3 focus:outline-none focus:ring-2 focus:ring-sky-300"
          rows={3}
          placeholder="Въведи естествен текст... (напр. Вечеря с Гери в неделя от 18 до 19:30)"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-sky-600 text-white px-4 py-2 hover:bg-sky-700 disabled:opacity-50"
          >
            {loading ? 'Мисля…' : 'Парсни'}
          </button>
          {preview && (
            <button
              type="button"
              onClick={handleSave}
              className="rounded-xl bg-emerald-600 text-white px-4 py-2 hover:bg-emerald-700"
            >Запази</button>
          )}
        </div>
      </form>

      {error && (
        <div className="mt-3 rounded-xl bg-red-50 text-red-700 p-3 text-sm">{error}</div>
      )}
      {savedMsg && (
        <div className="mt-3 rounded-xl bg-emerald-50 text-emerald-700 p-3 text-sm">{savedMsg}</div>
      )}

      {preview && (
        <div className="mt-4 rounded-xl border border-slate-200 p-3 bg-slate-50">
          <div className="text-sm text-slate-600">Преглед</div>
          <div className="font-medium">{preview.title}</div>
          <div className="text-sm">Начало: {formatDT(preview.start)}</div>
          <div className="text-sm">Край: {formatDT(preview.end)}</div>
        </div>
      )}
    </div>
  )
}