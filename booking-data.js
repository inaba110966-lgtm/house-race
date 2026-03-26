'use strict';
// MACHUA DESIGNERS SALON — Booking Data Layer (localStorage)

const MACHUA = (() => {

  /* ── Storage keys ────────────────────────────────────────── */
  const K = { bookings:'machua_bookings', courses:'machua_courses', schedule:'machua_schedule' };

  /* ── Defaults ────────────────────────────────────────────── */
  const DEF_COURSES = [
    {
      id:'cut', name:'カット', price:5000, minutes:30,
      options:[
        { id:'cut_perm',      name:'パーマ',        price:3000, minutes:60 },
        { id:'cut_color',     name:'カラー',         price:4000, minutes:45 },
        { id:'cut_treatment', name:'トリートメント', price:4000, minutes:45 },
      ]
    },
    { id:'color',     name:'カラー',         price:4000, minutes:90, options:[] },
    { id:'treatment', name:'トリートメント', price:5000, minutes:45, options:[] },
  ];

  const DEF_SCHEDULE = {
    closedDays:      [],
    capacity:        {},
    defaultCapacity: 1,
    adminEmail:      'admin@machua-salon.jp',
  };

  /* ── Persistence helpers ─────────────────────────────────── */
  const load    = (k, d) => { try { const v=localStorage.getItem(k); return v!==null?JSON.parse(v):d; } catch{ return d; } };
  const persist = (k, v) => localStorage.setItem(k, JSON.stringify(v));

  // Initialise defaults on first run
  if (!localStorage.getItem(K.courses))  persist(K.courses,  DEF_COURSES);
  if (!localStorage.getItem(K.schedule)) persist(K.schedule, DEF_SCHEDULE);
  if (!localStorage.getItem(K.bookings)) persist(K.bookings, []);

  /* ── Courses API ─────────────────────────────────────────── */
  const courses = {
    get:   ()    => load(K.courses, DEF_COURSES),
    set:   (d)   => persist(K.courses, d),
    find:  (id)  => courses.get().find(c => c.id === id) ?? null,
    reset: ()    => persist(K.courses, DEF_COURSES),
  };

  /* ── Schedule API ────────────────────────────────────────── */
  const schedule = {
    get:  ()     => load(K.schedule, DEF_SCHEDULE),
    set:  (d)    => persist(K.schedule, d),
    isClosed: dt => schedule.get().closedDays.includes(dt),
    cap:  dt     => { const s=schedule.get(); return Number(s.capacity[dt]??s.defaultCapacity); },
    setCap: (dt,v) => { const s=schedule.get(); s.capacity[dt]=Number(v); schedule.set(s); },
    toggleClosed: dt => {
      const s=schedule.get(); const i=s.closedDays.indexOf(dt);
      i===-1 ? s.closedDays.push(dt) : s.closedDays.splice(i,1);
      schedule.set(s);
    },
  };

  /* ── Bookings API ────────────────────────────────────────── */
  const bookings = {
    get:     ()    => load(K.bookings, []),
    set:     (d)   => persist(K.bookings, d),
    find:    id    => bookings.get().find(b=>b.id===id)??null,
    forDate: dt    => bookings.get().filter(b=>b.date===dt),
    remove:  id    => bookings.set(bookings.get().filter(b=>b.id!==id)),
    add: b => {
      b.id = Date.now().toString(36)+Math.random().toString(36).slice(2,5);
      b.createdAt = new Date().toISOString();
      const all=bookings.get(); all.push(b); bookings.set(all); return b;
    },
  };

  /* ── Slot utilities ──────────────────────────────────────── */
  const t2m = t => { const [h,m]=t.split(':').map(Number); return h*60+m; };
  const m2t = m => `${String(~~(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`;

  function getAllSlots() {
    const s=[]; for(let m=t2m('09:00'); m<t2m('20:00'); m+=30) s.push(m2t(m)); return s;
  }

  function getDateSlots(dt) {
    const slots=getAllSlots(), closed=schedule.isClosed(dt), cap=schedule.cap(dt), bks=bookings.forDate(dt);
    return slots.map(time => {
      if(closed) return { time, available:false, closed:true, bookings:[] };
      const sm=t2m(time);
      const over=bks.filter(b=>{ const s=t2m(b.startTime); return sm>=s&&sm<s+Number(b.totalMinutes); });
      return { time, available:over.length<cap, closed:false, bookings:over.filter(b=>b.startTime===time) };
    });
  }

  /* ── Date utilities ──────────────────────────────────────── */
  const DAY = ['日','月','火','水','木','金','土'];
  const toStr   = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const fromStr = s => { const [y,m,d]=s.split('-').map(Number); return new Date(y,m-1,d); };
  const today   = () => toStr(new Date());
  const weekOf  = dt => {
    const r=[],s=fromStr(dt); s.setDate(s.getDate()-s.getDay());
    for(let i=0;i<7;i++){const d=new Date(s);d.setDate(s.getDate()+i);r.push(toStr(d));} return r;
  };
  const fmt = dt => { const d=fromStr(dt); return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日（${DAY[d.getDay()]}）`; };
  const fmtShort = dt => { const d=fromStr(dt); return `${d.getMonth()+1}/${d.getDate()}(${DAY[d.getDay()]})`; };

  /* ── Email helpers (mailto fallback) ────────────────────── */
  function optNames(b) {
    return (b.optionIds||[]).map(id=>{
      for(const c of courses.get()){ const o=c.options.find(o=>o.id===id); if(o) return o.name; } return id;
    }).join('、');
  }
  function bookingText(b) {
    const c=courses.find(b.courseId); const opts=optNames(b);
    return [`日時: ${fmt(b.date)} ${b.startTime}`,`コース: ${c?.name??b.courseId}`,
      opts?`オプション: ${opts}`:null,`合計: ¥${Number(b.totalPrice).toLocaleString()} / ${b.totalMinutes}分`,
      `お名前: ${b.name}`,`電話: ${b.phone}`,`メール: ${b.email}`].filter(Boolean).join('\n');
  }
  function mailCustomer(b) {
    const s=encodeURIComponent(`【MACHUA】ご予約確定 ${fmt(b.date)} ${b.startTime}`);
    const body=encodeURIComponent(`${b.name} 様\n\nご予約ありがとうございます。\n\n▼ご予約内容\n${bookingText(b)}\n\nご来店お待ちしております。\nMACHUA DESIGNERS SALON\nTel: 0466-53-1202`);
    window.open(`mailto:${b.email}?subject=${s}&body=${body}`,'_blank');
  }
  function mailAdmin(b) {
    const ae=schedule.get().adminEmail||'admin@machua-salon.jp';
    const s=encodeURIComponent(`【MACHUA新規予約】${b.name}様 ${fmt(b.date)} ${b.startTime}`);
    const body=encodeURIComponent(`新規予約が入りました。\n\n${bookingText(b)}`);
    window.open(`mailto:${ae}?subject=${s}&body=${body}`,'_blank');
  }

  /* ── Admin auth ──────────────────────────────────────────── */
  const ADMIN_PASS = 'guroguro';
  const auth = {
    check: () => sessionStorage.getItem('machua_admin')==='1',
    login: pw => { if(pw===ADMIN_PASS){ sessionStorage.setItem('machua_admin','1'); return true; } return false; },
    logout: () => { sessionStorage.removeItem('machua_admin'); location.href='index.html'; },
  };

  return {
    courses, schedule, bookings,
    getAllSlots, getDateSlots,
    t2m, m2t, DAY,
    toStr, fromStr, today, weekOf, fmt, fmtShort,
    mailCustomer, mailAdmin, auth,
    DEF_COURSES,
  };
})();
