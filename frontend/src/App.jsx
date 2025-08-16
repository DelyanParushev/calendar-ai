import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { DateTime } from 'luxon';

const API_BASE = import.meta.env.VITE_API_BASE;

function App() {
  const [events, setEvents] = useState([]);
  const [newEventText, setNewEventText] = useState('');

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API_BASE}/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const handleAddEvent = async () => {
    if (!newEventText.trim()) return;

    try {
      const response = await axios.post(`${API_BASE}/parse`, { text: newEventText });
      setEvents([...events, response.data]);
      setNewEventText('');
    } catch (error) {
      console.error('Error adding event:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-4">AI Calendar</h1>

      <div className="mb-6 flex gap-2">
        <input
          type="text"
          value={newEventText}
          onChange={(e) => setNewEventText(e.target.value)}
          placeholder="Въведи събитие, напр. 'Вечеря с Гери в Неделя от 18'"
          className="flex-1 p-2 border border-gray-300 rounded"
        />
        <button
          onClick={handleAddEvent}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Добави
        </button>
      </div>

      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay'
        }}
        events={events.map(e => ({
          title: e.title,
          start: DateTime.fromISO(e.start).toISO(),
          end: e.end ? DateTime.fromISO(e.end).toISO() : undefined,
        }))}
        height="auto"
      />
    </div>
  );
}

export default App;
