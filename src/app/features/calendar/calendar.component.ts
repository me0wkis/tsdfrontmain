import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports for sidebar
import { ButtonModule } from 'primeng/button';

// Layout import
import { MainLayout } from '@core/layouts/main-layout/main-layout';

// FullCalendar imports
import { FullCalendarModule } from '@fullcalendar/angular';
import {
  CalendarOptions,
  DateSelectArg,
  EventClickArg,
  EventApi,
} from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  description?: string;
  allDay?: boolean;
  eventType?: 'workout' | 'social' | 'meeting' | 'personal';
}

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    FullCalendarModule,
    MainLayout,
    ButtonModule,
  ],
  templateUrl: './calendar.component.html',
  styleUrl: './calendar.component.css',
})
export class CalendarComponent implements OnInit {
  // FullCalendar configuration
  calendarOptions: CalendarOptions = {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'timeGridDay,timeGridWeek,dayGridMonth',
    },
    weekends: true,
    editable: true,
    selectable: true,
    selectMirror: true,
    dayMaxEvents: true,
    nowIndicator: true, // Show current time indicator
    locale: 'en',
    // Define business hours to shade non-business hours
    businessHours: {
      daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
      startTime: '08:00',
      endTime: '22:00',
    }, // Non-business hours shading
    slotMinTime: '00:00:00',
    slotMaxTime: '24:00:00',
    slotDuration: '00:30:00', // 30-minute slots for better resolution
    slotLabelFormat: {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      meridiem: false,
    },

    // Event appearance customization
    eventDidMount: this.customizeEventAppearance.bind(this),
    eventClassNames: this.getEventClassNames.bind(this), // Time format - use 24-hour format
    eventTimeFormat: {
      hour: '2-digit',
      minute: '2-digit',
      meridiem: false,
      hour12: false,
    },

    // Allow events to be selectable and scrollable
    eventInteractive: true,

    // Week numbers
    weekNumbers: true,
    weekNumberFormat: { week: 'numeric' },
    weekNumberCalculation: 'ISO',

    // First day of week - Monday
    firstDay: 1, // Button text customization
    buttonText: {
      today: 'Today',
      month: 'Month',
      week: 'Week',
      day: 'Day',
    }, // View customization
    views: {
      dayGridMonth: {
        titleFormat: { year: 'numeric', month: 'long' },
        dayHeaderFormat: { weekday: 'short' },
        eventTimeFormat: {
          // Specific time format for month view
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          meridiem: false,
        },
      },
      timeGridWeek: {
        titleFormat: { year: 'numeric', month: 'short' },
        dayHeaderFormat: { weekday: 'short', month: 'numeric', day: 'numeric' },
        eventTimeFormat: {
          // Specific time format for week view
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          meridiem: false,
        },
      },
      timeGridDay: {
        titleFormat: { year: 'numeric', month: 'long', day: 'numeric' },
        eventTimeFormat: {
          // Specific time format for day view
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          meridiem: false,
        },
      },
    },

    // Event handlers
    events: [],
    select: this.handleDateSelect.bind(this),
    eventClick: this.handleEventClick.bind(this),
    eventDrop: this.handleEventChange.bind(this),
    eventResize: this.handleEventChange.bind(this),
  };

  // Modal properties
  showEventModal = false;
  isClosing = false;
  currentEvent: CalendarEvent = this.createEmptyEvent();
  modalMode: 'create' | 'edit' = 'create';
  currentEvents: EventApi[] = [];
  showEndDate = false;

  ngOnInit(): void {
    this.loadEventsFromStorage();
  }

  // Handle date selection
  handleDateSelect(selectInfo: DateSelectArg) {
    this.modalMode = 'create';
    this.currentEvent = this.createEmptyEvent();
    this.currentEvent.start = selectInfo.startStr;
    if (selectInfo.endStr) {
      this.currentEvent.end = selectInfo.endStr;
      this.showEndDate = true;
    } else {
      this.showEndDate = false;
    }
    this.currentEvent.allDay = selectInfo.allDay;
    this.openEventModal();
  }
  // Handle event click
  handleEventClick(clickInfo: EventClickArg) {
    this.modalMode = 'edit';
    const event = clickInfo.event;
    this.currentEvent = {
      id: event.id,
      title: event.title,
      start: event.startStr,
      end: event.endStr,
      description: event.extendedProps['description'] || '',
      allDay: event.allDay,
      eventType: event.extendedProps['eventType'],
    };
    this.showEndDate = !!event.endStr;
    this.openEventModal();
  }

  // Handle event changes (drag, drop, resize)
  handleEventChange(changeInfo: any) {
    // Update event in storage
    const events = this.loadEventsFromLocalStorage();
    const index = events.findIndex((e) => e.id === changeInfo.event.id);

    if (index !== -1) {
      events[index] = {
        ...events[index],
        start: changeInfo.event.startStr,
        end: changeInfo.event.endStr,
        allDay: changeInfo.event.allDay,
      };
      this.saveEventsToLocalStorage(events);
    }
  }

  // Modal methods
  openEventModal() {
    this.showEventModal = true;
    this.isClosing = false;
    document.body.classList.add('modal-open');
  }

  closeEventModal() {
    this.isClosing = true;
    setTimeout(() => {
      this.showEventModal = false;
      this.isClosing = false;
      document.body.classList.remove('modal-open');
    }, 300); // Matching the animation duration in CSS
  }

  saveEvent() {
    if (!this.currentEvent.title.trim()) {
      return; // Don't save events without a title
    }

    const events = this.loadEventsFromLocalStorage();

    if (this.modalMode === 'create') {
      // Create new event
      this.currentEvent.id = this.generateEventId();
      events.push(this.currentEvent);
    } else {
      // Update existing event
      const index = events.findIndex((e) => e.id === this.currentEvent.id);
      if (index !== -1) {
        events[index] = this.currentEvent;
      }
    }

    // Save to storage and update calendar
    this.saveEventsToLocalStorage(events);
    this.loadEventsFromStorage();
    this.closeEventModal();
  }
  deleteEvent() {
    if (confirm('Are you sure you want to delete this event?')) {
      const events = this.loadEventsFromLocalStorage();
      const filteredEvents = events.filter(
        (e) => e.id !== this.currentEvent.id
      );
      this.saveEventsToLocalStorage(filteredEvents);
      this.loadEventsFromStorage();
      this.closeEventModal();
    }
  }

  // Date and time utilities
  getDateStringFromISO(isoString: string): string {
    if (!isoString) return '';
    return isoString.split('T')[0];
  }

  getTimeStringFromISO(isoString: string): string {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toTimeString().substring(0, 5); // Format: HH:MM
  }

  updateEventDate(event: any, field: 'start' | 'end') {
    const newDate = event.target.value;
    if (!newDate) return;

    const currentValue =
      field === 'start'
        ? this.currentEvent.start
        : this.currentEvent.end || this.currentEvent.start;
    const currentTime = this.getTimeStringFromISO(currentValue);

    const dateTime =
      newDate + (this.currentEvent.allDay ? '' : `T${currentTime || '00:00'}`);

    if (field === 'start') {
      this.currentEvent.start = dateTime;
      // If end date exists and is now before start date, adjust it
      if (this.currentEvent.end && this.currentEvent.end < dateTime) {
        this.currentEvent.end = dateTime;
      }
    } else {
      this.currentEvent.end = dateTime;
    }
  }

  updateEventTime(event: any, field: 'start' | 'end') {
    const newTime = event.target.value;
    if (!newTime) return;

    const currentValue =
      field === 'start'
        ? this.currentEvent.start
        : this.currentEvent.end || this.currentEvent.start;
    const currentDate = this.getDateStringFromISO(currentValue);

    const dateTime = currentDate + `T${newTime}:00`;

    if (field === 'start') {
      this.currentEvent.start = dateTime;
      // If end time exists and is now before start time, adjust it
      if (this.currentEvent.end && this.currentEvent.end < dateTime) {
        this.currentEvent.end = this.addDefaultDuration(dateTime);
      }
    } else {
      this.currentEvent.end = dateTime;
    }
  }

  addDefaultDuration(isoString: string): string {
    if (!isoString) return '';
    const date = new Date(isoString);
    date.setHours(date.getHours() + 1);
    return date.toISOString();
  }

  onAllDayChange() {
    if (this.currentEvent.allDay) {
      // Convert to all-day event format
      this.currentEvent.start = this.getDateStringFromISO(
        this.currentEvent.start
      );
      if (this.currentEvent.end) {
        this.currentEvent.end = this.getDateStringFromISO(
          this.currentEvent.end
        );
      }
    } else {
      // Add default time for non-all-day events
      const startDate = this.getDateStringFromISO(this.currentEvent.start);
      this.currentEvent.start = `${startDate}T09:00:00`;

      if (this.currentEvent.end) {
        const endDate = this.getDateStringFromISO(this.currentEvent.end);
        this.currentEvent.end = `${endDate}T10:00:00`;
      }
    }
  } // Метод для кастомизации внешнего вида событий
  customizeEventAppearance(info: any) {
    // Получаем ссылку на DOM-элемент события
    const eventEl = info.el;
    const event = info.event;

    // Убираем скругление углов для всех событий
    eventEl.style.borderRadius = '0';

    // Устанавливаем темный цвет текста для всех событий
    eventEl.style.color = '#333333';

    // Проверяем тип события и применяем соответствующие стили
    const eventType = event.extendedProps?.eventType;

    if (eventType === 'workout') {
      eventEl.style.backgroundColor = '#ffebee';
      eventEl.style.borderLeft = '4px solid #f43f5e';
    } else if (eventType === 'social') {
      eventEl.style.backgroundColor = '#e8f5e9';
      eventEl.style.borderLeft = '4px solid #4caf50';
    } else if (eventType === 'meeting') {
      eventEl.style.backgroundColor = '#e3f2fd';
      eventEl.style.borderLeft = '4px solid #2196f3';
    } else if (eventType === 'personal') {
      eventEl.style.backgroundColor = '#fff8e1';
      eventEl.style.borderLeft = '4px solid #ffc107';
    } else {
      // Если тип не указан явно
      if (event.allDay) {
        // Применяем стили для полнодневных событий
        eventEl.style.backgroundColor = '#EFF6FF'; // Светло-синий
        eventEl.style.borderLeft = '4px solid #3B82F6'; // Синий
      } else {
        // Автоматическое определение типа по названию
        const title = event.title.toLowerCase();

        if (
          title.includes('training') ||
          title.includes('sport') ||
          title.includes('fitness') ||
          title.includes('workout') ||
          title.includes('gym')
        ) {
          eventEl.style.backgroundColor = '#ffebee';
          eventEl.style.borderLeft = '4px solid #f43f5e';
        } else if (
          title.includes('meeting') ||
          title.includes('lunch') ||
          title.includes('dinner') ||
          title.includes('coffee') ||
          title.includes('party')
        ) {
          eventEl.style.backgroundColor = '#e8f5e9';
          eventEl.style.borderLeft = '4px solid #4caf50';
        } else if (
          title.includes('call') ||
          title.includes('conference') ||
          title.includes('presentation') ||
          title.includes('report')
        ) {
          eventEl.style.backgroundColor = '#e3f2fd';
          eventEl.style.borderLeft = '4px solid #2196f3';
        } else if (
          title.includes('doctor') ||
          title.includes('appointment') ||
          title.includes('personal') ||
          title.includes('family') ||
          title.includes('home')
        ) {
          eventEl.style.backgroundColor = '#fff8e1';
          eventEl.style.borderLeft = '4px solid #ffc107';
        } else {
          // Генерируем цвет на основе названия события
          const color = this.getColorFromString(event.title);
          eventEl.style.backgroundColor = color;
        }
      }
    }

    // Если у события есть описание, добавляем тултип
    if (event.extendedProps && event.extendedProps.description) {
      eventEl.title = event.extendedProps.description;
    }
  }

  // Метод для получения цвета на основе строки (названия события)
  getColorFromString(str: string): string {
    if (!str) return '#3B82F6'; // Возвращаем синий по умолчанию

    // Генерируем хеш из строки
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Преобразуем хеш в цвет
    const colors = [
      '#3B82F6', // Синий
      '#10B981', // Зеленый
      '#F59E0B', // Оранжевый
      '#EF4444', // Красный
      '#8B5CF6', // Фиолетовый
      '#EC4899', // Розовый
      '#06B6D4', // Голубой
      '#F97316', // Темно-оранжевый
      '#84CC16', // Лаймовый
    ];

    // Выбираем цвет из палитры на основе хеша
    return colors[Math.abs(hash) % colors.length];
  }
  // Метод для добавления классов к событиям
  getEventClassNames(info: any) {
    const classes = ['custom-event'];
    const eventType = info.event.extendedProps?.eventType;

    // Если тип события указан явно, используем его
    if (eventType) {
      classes.push(`${eventType}-event`);
      return classes;
    }

    // Если тип не указан, выполняем автоопределение
    const title = info.event.title.toLowerCase();

    // Добавляем классы в зависимости от свойств события
    if (info.event.allDay) {
      classes.push('all-day-event');
      return classes;
    } // Автоматическая категоризация событий по ключевым словам
    if (
      title.includes('training') ||
      title.includes('sport') ||
      title.includes('fitness') ||
      title.includes('workout') ||
      title.includes('gym') ||
      title.includes('exercise')
    ) {
      classes.push('workout-event');
    } else if (
      title.includes('meeting') ||
      title.includes('lunch') ||
      title.includes('dinner') ||
      title.includes('coffee') ||
      title.includes('brunch') ||
      title.includes('friends') ||
      title.includes('party')
    ) {
      classes.push('social-event');
    } else if (
      title.includes('совещание') ||
      title.includes('call') ||
      title.includes('conference') ||
      title.includes('meeting') ||
      title.includes('presentation') ||
      title.includes('report') ||
      title.includes('discussion')
    ) {
      classes.push('meeting-event');
    } else if (
      title.includes('doctor') ||
      title.includes('appointment') ||
      title.includes('personal') ||
      title.includes('home') ||
      title.includes('family')
    ) {
      classes.push('personal-event');
    } else {
      // Если не подошло ни под одну категорию, используем цвет по умолчанию
      const eventId = parseInt(info.event.id, 10) % 4;
      if (eventId === 0) classes.push('workout-event');
      else if (eventId === 1) classes.push('social-event');
      else if (eventId === 2) classes.push('meeting-event');
      else classes.push('personal-event');
    }

    return classes;
  }

  // Метод для определения яркости цвета
  getBrightness(color: string): number {
    // Преобразуем hex в RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);

    // Формула для расчета яркости
    return (r * 299 + g * 587 + b * 114) / 1000;
  }
  // Метод для установки типа события
  setEventType(type: 'workout' | 'social' | 'meeting' | 'personal') {
    this.currentEvent.eventType = type;
  }

  // Helper methods
  createEmptyEvent(): CalendarEvent {
    return {
      id: '',
      title: '',
      start: '',
      description: '',
      allDay: false,
      eventType: undefined,
    };
  }

  generateEventId(): string {
    return Date.now().toString() + Math.floor(Math.random() * 1000);
  }

  // Storage methods
  loadEventsFromStorage() {
    const events = this.loadEventsFromLocalStorage();

    if (events.length === 0) {
      this.loadSampleEvents();
    } else {
      this.calendarOptions.events = events;
    }
  }

  loadEventsFromLocalStorage(): CalendarEvent[] {
    const storedEvents = localStorage.getItem('calendar-events');
    if (storedEvents) {
      try {
        return JSON.parse(storedEvents);
      } catch (error) {
        console.error('Error parsing events from localStorage', error);
        return [];
      }
    }
    return [];
  }

  saveEventsToLocalStorage(events: CalendarEvent[]) {
    localStorage.setItem('calendar-events', JSON.stringify(events));
  }

  loadSampleEvents() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    const dayAfterTomorrow = new Date(today);
    dayAfterTomorrow.setDate(today.getDate() + 2);

    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);

    // Set specific times for today's events
    const meetingStart = new Date(today);
    meetingStart.setHours(10, 0, 0);

    const lunchStart = new Date(today);
    lunchStart.setHours(13, 0, 0);

    const lunchEnd = new Date(today);
    lunchEnd.setHours(14, 0, 0);

    const workoutStart = new Date(today);
    workoutStart.setHours(18, 0, 0);

    const workoutEnd = new Date(today);
    workoutEnd.setHours(19, 30, 0);

    // Set times for tomorrow's events
    const doctorStart = new Date(tomorrow);
    doctorStart.setHours(9, 0, 0);

    const doctorEnd = new Date(tomorrow);
    doctorEnd.setHours(10, 0, 0);

    const projectStart = new Date(tomorrow);
    projectStart.setHours(14, 0, 0);

    const projectEnd = new Date(tomorrow);
    projectEnd.setHours(17, 0, 0);
    const sampleEvents: CalendarEvent[] = [
      {
        id: this.generateEventId(),
        title: 'Team Meeting',
        start: meetingStart.toISOString(),
        end: new Date(meetingStart.getTime() + 90 * 60000).toISOString(),
        description: 'Weekly team meeting to discuss current project tasks',
        allDay: false,
      },
      {
        id: this.generateEventId(),
        title: 'Lunch with Client',
        start: lunchStart.toISOString(),
        end: lunchEnd.toISOString(),
        description: 'Discussing new contract at "Metropol" restaurant',
        allDay: false,
      },
      {
        id: this.generateEventId(),
        title: 'Gym Workout',
        start: workoutStart.toISOString(),
        end: workoutEnd.toISOString(),
        description: 'Strength training + cardio',
        allDay: false,
      },
      {
        id: this.generateEventId(),
        title: 'Doctor Appointment',
        start: doctorStart.toISOString(),
        end: doctorEnd.toISOString(),
        description: 'Annual medical checkup',
        allDay: false,
      },
      {
        id: this.generateEventId(),
        title: 'Project Deadline',
        start: projectStart.toISOString(),
        end: projectEnd.toISOString(),
        description: 'Final project presentation for management',
        allDay: false,
      },
      {
        id: this.generateEventId(),
        title: 'AI Conference',
        start: dayAfterTomorrow.toISOString(),
        description: 'International conference on artificial intelligence',
        allDay: true,
      },
      {
        id: this.generateEventId(),
        title: "Alex's Birthday",
        start: nextWeek.toISOString(),
        description: 'Celebration at "Aist" restaurant at 19:00',
        allDay: true,
      },
    ];

    this.saveEventsToLocalStorage(sampleEvents);
    this.calendarOptions.events = sampleEvents;
  }
}
