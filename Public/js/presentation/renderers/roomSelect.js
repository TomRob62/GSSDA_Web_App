export function populateRoomSelect(select, rooms) {
  select.innerHTML = '';
  select.appendChild(new Option('-- Select Room --', ''));
  rooms.forEach((room) => {
    const option = new Option(room.room_number, room.id);
    select.appendChild(option);
  });
}
