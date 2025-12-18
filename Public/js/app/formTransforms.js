import { normalizeDuration } from '../components/datetime.js';
import { createProfileFormData } from './profiles/formData.js';

function formDataToObject(form) {
  const payload = {};
  new FormData(form).forEach((value, key) => {
    if (Object.prototype.hasOwnProperty.call(payload, key)) {
      const current = payload[key];
      if (Array.isArray(current)) {
        current.push(value);
      } else {
        payload[key] = [current, value];
      }
      return;
    }
    payload[key] = value;
  });
  return payload;
}

function parseDuration(form) {
  const hoursField = form.querySelector('select[name="duration_hours"]');
  const minutesField = form.querySelector('select[name="duration_minutes"]');
  const hours = parseInt(hoursField?.value || '0', 10);
  const minutes = parseInt(minutesField?.value || '0', 10);
  return normalizeDuration(hours * 60 + minutes);
}

function transformRooms(form, payload) {
  const staticSelect = form.querySelector('#staticSelect');
  const isStatic = staticSelect ? staticSelect.value === 'yes' : true;
  const manager = form.__descriptionManager;
  if (!manager) {
    throw new Error('The room form is missing its description manager.');
  }

  manager.clearError();

  const roomNumber = payload.room_number ? payload.room_number.trim() : '';
  if (!roomNumber) {
    throw new Error('Please provide a room number.');
  }

  if (isStatic) {
    const description = manager.getStaticDescription();
    if (!description) {
      manager.showError('Please enter a description for the static room.');
      throw new Error('A static room requires a description.');
    }
    return {
      payload: {
        room_number: roomNumber,
        static: true,
        descriptions: [
          {
            description,
            start_time: null,
            end_time: null,
          },
        ],
      },
    };
  }

  const entries = manager.getEntries();
  if (!entries.length) {
    manager.showError('Add at least one time-bound description for a non-static room.');
    throw new Error('Non-static rooms must include at least one description.');
  }

  return {
    payload: {
      room_number: roomNumber,
      static: false,
      descriptions: entries.map((entry) => ({
        description: entry.description,
        start_time: entry.start_time,
        end_time: entry.end_time,
      })),
    },
  };
}

function transformCaller(form, payload) {
  // mc is now a select with values 'yes' or 'no'
  const mcSelect = form.querySelector('#mcSelect');
  const mcChecked = (mcSelect ? mcSelect.value === 'yes' : false);
  const danceTypes = payload.dance_types
    ? payload.dance_types.split(',').map((value) => value.trim()).filter(Boolean)
    : [];
  return {
    payload: {
      first_name: payload.first_name,
      last_name: payload.last_name,
      suffix: payload.suffix || '',
      mc: mcChecked,
      dance_types: danceTypes,
    },
  };
}

function applyDurationFields(payload, durationMinutes) {
  const startDate = payload.start ? new Date(payload.start) : null;
  if (!startDate) return { payload: { ...payload, start: null, end: null } };
  const endDate = new Date(startDate.getTime() + durationMinutes * 60000);
  return {
    payload: { ...payload, start: startDate.toISOString(), end: endDate.toISOString() },
    nextStart: endDate,
  };
}

function transformEvent(form, payload) {
  const durationMinutes = parseDuration(form);
  const danceTypes = payload.dance_types
    ? payload.dance_types.split(',').map((value) => value.trim()).filter(Boolean)
    : [];
  const callerValues = payload.caller_cuer_ids;
  const callerArray = Array.isArray(callerValues)
    ? callerValues
    : callerValues
      ? [callerValues]
      : [];
  const callerIds = callerArray
    .map((value) => Number(value))
    .filter((value) => !Number.isNaN(value));
  const base = {
    room_id: Number(payload.room_id),
    caller_cuer_ids: callerIds,
    start: payload.start,
    dance_types: danceTypes,
  };
  return applyDurationFields(base, durationMinutes);
}

function transformMc(form, payload) {
  const durationMinutes = parseDuration(form);
  const base = {
    room_id: Number(payload.room_id),
    caller_cuer_id: payload.caller_cuer_id ? Number(payload.caller_cuer_id) : payload.caller_cuer_id,
    start: payload.start,
  };
  return applyDurationFields(base, durationMinutes);
}

function transformProfile(form, payload) {
  const formData = createProfileFormData(form, payload);
  return { payload: formData, isMultipart: true };
}

export function buildPayload(type, form) {
  const payload = formDataToObject(form);
  if (type === 'rooms') return transformRooms(form, payload);
  if (type === 'caller_cuers') return transformCaller(form, payload);
  if (type === 'events') return transformEvent(form, payload);
  if (type === 'mcs') return transformMc(form, payload);
  if (type === 'profiles') return transformProfile(form, payload);
  return { payload };
}
