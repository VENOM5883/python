// Загрузка расписания врача через REST API
async function loadSchedule(doctorId, date) {
  const response = await fetch(`/doctors/${doctorId}/schedule?date=${date}`);
  const data = await response.json();
  document.querySelector("#schedule").textContent =
    data.slots.map(s => `${s.time} — ${s.status}`).join("\n");
}
