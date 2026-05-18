// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  Prajna — Shared Application Logic
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ─── Global State ───
let chatHistory = [];
let uploadedImages = [];
let currentMode = 'fast';
let currentLanguage = localStorage.getItem('prajna_lang') || 'Hindi';
let currentConversationId = null; // active conversation ID
let saveChatsEnabled = localStorage.getItem('prajna_save_chats') !== 'false'; // default: on

// ─── Dummy data for hackathon demo ───
function generateDummyActivityData() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const todayDate = today.getDate();
  const activityMap = {};
  for (let day = 1; day < todayDate; day++) {
    const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
    if (day >= todayDate - 12) {
      activityMap[dateStr] = Math.floor(Math.random() * 3) + 3;
    } else if (day >= todayDate - 18) {
      if (Math.random() > 0.3) activityMap[dateStr] = Math.floor(Math.random() * 3) + 1;
    } else {
      if (Math.random() > 0.6) activityMap[dateStr] = Math.floor(Math.random() * 2) + 1;
    }
  }
  const todayStr = `${year}-${String(month+1).padStart(2,'0')}-${String(todayDate).padStart(2,'0')}`;
  activityMap[todayStr] = 4;
  return activityMap;
}
const DUMMY_ACTIVITY = generateDummyActivityData();
const DUMMY_STREAK = 12;
const DUMMY_HIGHEST_STREAK = 18;
const DUMMY_BADGES = [
  { icon: '🥈', label: 'Week Warrior', labelHi: 'सप्ताह योद्धा', desc: '7-day streak', descHi: '7 दिन की स्ट्रीक' },
  { icon: '🥉', label: '3-Day Starter', labelHi: '3 दिन की शुरुआत', desc: '3-day streak', descHi: '3 दिन की स्ट्रीक' },
  { icon: '🎯', label: 'Quiz Master', labelHi: 'क्विज़ मास्टर', desc: '10 quizzes aced', descHi: '10 क्विज़ पास' },
  { icon: '📚', label: 'Bookworm', labelHi: 'किताबी कीड़ा', desc: '20 topics covered', descHi: '20 विषय पूरे' },
  { icon: '⚡', label: 'Speed Learner', labelHi: 'तेज़ सीखने वाला', desc: '5 topics in a day', descHi: 'एक दिन में 5 विषय' },
];

// ─── Auth Gate ───
(function authGate() {
  const studentId = localStorage.getItem('prajna_student_id');
  const onLoginPage = location.pathname.includes('login.html') || location.pathname === '/';

  if (!studentId && !onLoginPage) {
    location.href = 'login.html';
    return;
  }

  // Set avatar initials
  if (studentId) {
    const name = localStorage.getItem('prajna_name') || 'User';
    const av = document.getElementById('navAvatar');
    if (av) {
      const parts = name.trim().split(/\s+/);
      av.textContent = parts[0] ? (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase() : '?';
    }
    // Load sidebar data
    if (!onLoginPage) {
      loadSidebarData();
    }
  }
})();

// ─── Translation helper ───
function t(en, hi) {
  return currentLanguage === 'English' ? en : hi;
}

function updateUILanguage() {
  document.querySelectorAll('[data-en]').forEach(el => {
    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') return; // skip form elements
    el.innerHTML = currentLanguage === 'English' ? el.dataset.en : el.dataset.hi;
  });

  // Switch ALL element placeholders (inputs, textareas) that have data-placeholder-en
  document.querySelectorAll('[data-placeholder-en]').forEach(el => {
    el.placeholder = currentLanguage === 'English'
      ? (el.dataset.placeholderEn || '')
      : (el.dataset.placeholderHi || el.dataset.placeholderEn || '');
  });

  // Re-calculate mode slider after text width changes
  setTimeout(() => setMode(currentMode), 50);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  LOGIN PAGE — Tab Switcher
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function switchTab(tab) {
  const signinTab = document.getElementById('tabSignin');
  const signupTab = document.getElementById('tabSignup');
  const slider    = document.getElementById('tabSlider');
  const formIn    = document.getElementById('formSignin');
  const formUp    = document.getElementById('formSignup');
  if (!signinTab) return;

  if (tab === 'signin') {
    signinTab.classList.add('active');
    signupTab.classList.remove('active');
    slider.classList.remove('right');
    formIn.style.display = 'block';
    formUp.style.display = 'none';
  } else {
    signupTab.classList.add('active');
    signinTab.classList.remove('active');
    slider.classList.add('right');
    formIn.style.display = 'none';
    formUp.style.display = 'block';
  }
}

function togglePw(fieldId, btn) {
  const input = document.getElementById(fieldId);
  if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
  else { input.type = 'password'; btn.textContent = '👁'; }
}

// ─── Sign In (DB-backed) ───
async function handleSignin(e) {
  e.preventDefault();
  const email = document.getElementById('si-email');
  const pass  = document.getElementById('si-password');

  clearFieldError(email, 'si-email-err');
  clearFieldError(pass, 'si-password-err');

  if (!email.value.trim()) { showFieldError(email, 'si-email-err', 'Name is required'); return; }
  if (!pass.value) { showFieldError(pass, 'si-password-err', 'Password is required'); return; }

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: email.value.trim(), password: pass.value }),
    });
    const data = await res.json();

    if (!res.ok) {
      showFieldError(pass, 'si-password-err', data.error || 'Login failed');
      return;
    }

    localStorage.setItem('prajna_student_id', data.student_id);
    localStorage.setItem('prajna_name', data.name);
    localStorage.setItem('prajna_streak', data.streak);
    location.href = 'index.html';
  } catch (err) {
    showFieldError(pass, 'si-password-err', 'Server not running. Start with run.bat');
  }
}

// ─── Sign Up (DB-backed — same endpoint, auto-creates) ───
async function handleSignup(e) {
  e.preventDefault();
  const name    = document.getElementById('su-name');
  const email   = document.getElementById('su-email');
  const pass    = document.getElementById('su-password');
  const confirm = document.getElementById('su-confirm');

  clearFieldError(name, 'su-name-err');
  clearFieldError(email, 'su-email-err');
  clearFieldError(pass, 'su-password-err');
  clearFieldError(confirm, 'su-confirm-err');

  if (!name.value.trim()) { showFieldError(name, 'su-name-err', 'Name is required'); return; }
  if (!pass.value || pass.value.length < 3) { showFieldError(pass, 'su-password-err', 'Minimum 3 characters'); return; }
  if (pass.value !== confirm.value) { showFieldError(confirm, 'su-confirm-err', 'Passwords do not match'); return; }

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.value.trim(), password: pass.value }),
    });
    const data = await res.json();

    if (!res.ok) {
      showFieldError(pass, 'su-password-err', data.error || 'Signup failed');
      return;
    }

    localStorage.setItem('prajna_student_id', data.student_id);
    localStorage.setItem('prajna_name', data.name);
    localStorage.setItem('prajna_streak', data.streak);
    location.href = 'index.html';
  } catch (err) {
    showFieldError(pass, 'su-password-err', 'Server not running. Start with run.bat');
  }
}

function showFieldError(input, errId, msg) {
  input.classList.add('error');
  const el = document.getElementById(errId);
  if (el) { el.textContent = msg; el.classList.add('visible'); }
}
function clearFieldError(input, errId) {
  input.classList.remove('error', 'success');
  const el = document.getElementById(errId);
  if (el) { el.textContent = ''; el.classList.remove('visible'); }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SIDEBAR
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const hamburger = document.getElementById('hamburgerBtn');
const sidebarClose = document.getElementById('sidebarClose');

function toggleSidebar() {
  if (!sidebar) return;
  sidebar.classList.toggle('open');
  overlay.classList.toggle('open');
}

if (hamburger) hamburger.addEventListener('click', toggleSidebar);
if (sidebarClose) sidebarClose.addEventListener('click', toggleSidebar);
if (overlay) overlay.addEventListener('click', toggleSidebar);

function closeSidebar() {
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
}

async function loadSidebarData() {
  const studentId = localStorage.getItem('prajna_student_id');
  const name = localStorage.getItem('prajna_name') || 'User';
  if (!studentId) return;

  // Set name & avatar
  const sName = document.getElementById('sidebarName');
  const sAvatar = document.getElementById('sidebarAvatar');
  if (sName) sName.textContent = name;
  if (sAvatar) {
    const parts = name.trim().split(/\s+/);
    sAvatar.textContent = parts[0] ? (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase() : '?';
  }

  // Use dummy data for streak (merge with real data if available)
  let streak = DUMMY_STREAK;
  let badges = DUMMY_BADGES;

  try {
    const res = await fetch(`/api/progress/${studentId}`);
    const data = await res.json();
    // Use real streak if higher, otherwise keep dummy
    if (data.streak > streak) streak = data.streak;
  } catch (e) { /* use dummy */ }

  const sStreak = document.getElementById('sidebarStreak');
  if (sStreak) sStreak.textContent = `🔥 ${streak} Days`;

  // Render badges
  const badgesSection = document.getElementById('badgesSection');
  const badgesList = document.getElementById('badgesList');
  if (badgesList) {
    badgesList.innerHTML = badges.map((b, i) => `
      <div class="badge-card" style="animation-delay:${i * 0.08}s">
        <span class="badge-icon">${b.icon}</span>
        <div class="badge-info">
          <span class="badge-label" data-en="${b.label}" data-hi="${b.labelHi}">${currentLanguage === 'English' ? b.label : b.labelHi}</span>
          <span class="badge-desc" data-en="${b.desc}" data-hi="${b.descHi}">${currentLanguage === 'English' ? b.desc : b.descHi}</span>
        </div>
      </div>
    `).join('');
    if (badgesSection) badgesSection.style.display = 'block';
  }

  // Render calendar with dummy heatmap data (merge with real)
  let activityMap = { ...DUMMY_ACTIVITY };
  try {
    const res = await fetch(`/api/calendar/${studentId}`);
    const data = await res.json();
    // Merge real active dates into the map
    (data.active_dates || []).forEach(d => {
      if (!activityMap[d]) activityMap[d] = 2;
    });
  } catch (e) { /* use dummy only */ }

  renderCalendar(activityMap);

  // Load conversation list
  await loadConversations(studentId);

  // Apply language
  updateUILanguage();
}

// ─── Collapsible Sections ───
function toggleSection(btn) {
  const body = btn.nextElementSibling;
  if (body.style.display === 'none') {
    body.style.display = 'block';
    btn.classList.add('open');
  } else {
    body.style.display = 'none';
    btn.classList.remove('open');
  }
}

// ─── Save Chats Toggle ───
function toggleSaveChats(enabled) {
  saveChatsEnabled = enabled;
  localStorage.setItem('prajna_save_chats', enabled ? 'true' : 'false');
  const list = document.getElementById('conversationList');
  if (list) list.style.display = enabled ? '' : 'none';
  if (!enabled) {
    currentConversationId = null; // stop saving to current conversation
  }
}

// Restore toggle state on page load
window.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('saveChatToggle');
  if (toggle) {
    toggle.checked = saveChatsEnabled;
    toggleSaveChats(saveChatsEnabled);
  }
});
async function loadConversations(studentId) {
  if (!studentId) return;
  try {
    const res = await fetch(`/api/conversations/${studentId}`);
    const list = await res.json();
    renderConversationList(list);
  } catch(e) {}
}

function renderConversationList(list) {
  const el = document.getElementById('conversationList');
  if (!el) return;
  if (!list || list.length === 0) {
    el.innerHTML = `<div style="padding:10px 4px;font-size:12px;color:var(--text-muted)">${currentLanguage === 'Hindi' ? 'कोई पुरानी चैट नहीं' : 'No past chats yet'}</div>`;
    return;
  }
  el.innerHTML = list.map(c => {
    const active = c.conversation_id === currentConversationId ? ' convo-item--active' : '';
    return `<div class="convo-item${active}" onclick="switchConversation(${c.conversation_id})">
      <span class="convo-item__title">${escapeHtml(c.title)}</span>
      <button class="convo-item__del" onclick="deleteConvoItem(event,${c.conversation_id})" title="Delete">✕</button>
    </div>`;
  }).join('');
}

async function createNewChat() {
  const studentId = parseInt(localStorage.getItem('prajna_student_id'));
  if (!studentId) return;
  try {
    const res = await fetch('/api/conversations', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({student_id: studentId})
    });
    const data = await res.json();
    currentConversationId = data.conversation_id;
    // Clear chat UI
    chatHistory = [];
    const msgs = document.getElementById('chatMessages');
    if (msgs) msgs.innerHTML = '';
    closeSidebar();
    await loadConversations(studentId);
  } catch(e) { console.error('createNewChat failed', e); }
}

async function switchConversation(conversationId) {
  currentConversationId = conversationId;
  const studentId = parseInt(localStorage.getItem('prajna_student_id'));
  // Update active state in list
  await loadConversations(studentId);
  // Load messages
  try {
    const res = await fetch(`/api/conversations/${conversationId}/messages`);
    const messages = await res.json();
    chatHistory = messages.map(m => ({role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content}));
    const msgs = document.getElementById('chatMessages');
    if (msgs) {
      msgs.innerHTML = '';
      messages.forEach(m => appendMessage(m.role === 'assistant' ? 'bot' : 'user', m.content));
    }
  } catch(e) {}
  closeSidebar();
}

async function deleteConvoItem(e, conversationId) {
  e.stopPropagation();
  await fetch(`/api/conversations/${conversationId}`, {method:'DELETE'});
  if (currentConversationId === conversationId) {
    currentConversationId = null;
    chatHistory = [];
    const msgs = document.getElementById('chatMessages');
    if (msgs) msgs.innerHTML = '';
  }
  const studentId = parseInt(localStorage.getItem('prajna_student_id'));
  await loadConversations(studentId);
}

// ─── Heatmap Calendar ───
function renderCalendar(activityMap) {
  const container = document.getElementById('miniCalendar');
  if (!container) return;

  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const monthNames = ['January','February','March','April','May','June',
    'July','August','September','October','November','December'];

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayDate = today.getDate();

  const dayHeaders = ['Su','Mo','Tu','We','Th','Fr','Sa'];

  // Streak counter
  let currentStreak = 0;
  for (let d = todayDate; d >= 1; d--) {
    const ds = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    if (activityMap[ds]) currentStreak++;
    else break;
  }

  let html = `<div class="cal-header">
    <span class="cal-month">${monthNames[month]} ${year}</span>
    <span class="cal-streak-badge">🔥 ${currentStreak} day streak</span>
  </div>`;
  html += '<table><tr>';
  dayHeaders.forEach(d => { html += `<th>${d}</th>`; });
  html += '</tr><tr>';

  // Empty cells before first day
  for (let i = 0; i < firstDay; i++) {
    html += '<td><div class="cal-day cal-day--empty"></div></td>';
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
    const isToday = (day === todayDate);
    const activity = activityMap[dateStr] || 0;
    const isFuture = day > todayDate;

    let cls = 'cal-day--none';
    let tooltip = dateStr;
    if (isFuture) {
      cls = 'cal-day--future';
      tooltip += ' (upcoming)';
    } else if (isToday) {
      cls = 'cal-day--today';
      tooltip += ` — ${activity} sessions (today)`;
    } else if (activity >= 4) {
      cls = 'cal-day--high';
      tooltip += ` — ${activity} sessions`;
    } else if (activity >= 2) {
      cls = 'cal-day--active';
      tooltip += ` — ${activity} sessions`;
    } else if (activity >= 1) {
      cls = 'cal-day--low';
      tooltip += ` — ${activity} session`;
    }

    html += `<td><div class="cal-day ${cls}" title="${tooltip}">${day}</div></td>`;

    if ((firstDay + day) % 7 === 0 && day < daysInMonth) html += '</tr><tr>';
  }

  html += '</tr></table>';
  container.innerHTML = html;
}

// ─── Language Toggle ───
function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem('prajna_lang', lang);

  // Sync ALL toggle instances (navbar + sidebar)
  document.querySelectorAll('.lang-btn').forEach(btn => {
    if (btn.dataset.lang === lang) btn.classList.add('active');
    else btn.classList.remove('active');
  });
  document.querySelectorAll('.lang-slider').forEach(slider => {
    if (lang === 'English') slider.classList.add('right');
    else slider.classList.remove('right');
  });

  updateUILanguage();
}

// ─── Logout ───
function logout() {
  localStorage.removeItem('prajna_student_id');
  localStorage.removeItem('prajna_name');
  localStorage.removeItem('prajna_streak');
  location.href = 'login.html';
}

// ─── Toast ───
function showToast(msg) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  CHAT — Textarea Auto-resize
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const textarea = document.getElementById('chatTextarea');
const sendBtn  = document.getElementById('sendBtn');

if (textarea) {
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
    updateSendBtn();
  });
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });
}

function updateSendBtn() {
  if (!sendBtn) return;
  const hasText = textarea && textarea.value.trim().length > 0;
  const hasImg  = uploadedImages.length > 0;
  if (hasText || hasImg) {
    sendBtn.classList.remove('disabled'); sendBtn.classList.add('enabled'); sendBtn.disabled = false;
  } else {
    sendBtn.classList.remove('enabled'); sendBtn.classList.add('disabled'); sendBtn.disabled = true;
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  CHAT — Image Upload
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const attachBtn   = document.getElementById('attachBtn');
const fileInput   = document.getElementById('fileInput');
const imgPreviews = document.getElementById('imgPreviews');

if (attachBtn) attachBtn.addEventListener('click', () => fileInput.click());
if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    for (const file of e.target.files) {
      if (uploadedImages.length >= 4) break;
      const reader = new FileReader();
      reader.onload = (ev) => {
        uploadedImages.push({ name: file.name, data: ev.target.result });
        renderImagePreviews(); updateSendBtn();
      };
      reader.readAsDataURL(file);
    }
    fileInput.value = '';
  });
}

function renderImagePreviews() {
  if (!imgPreviews) return;
  imgPreviews.innerHTML = '';
  uploadedImages.forEach((img, i) => {
    const chip = document.createElement('div');
    chip.className = 'img-chip';
    chip.innerHTML = `<img src="${img.data}" alt="${img.name}">
      <span class="img-chip-name">${img.name}</span>
      <button class="img-chip-remove" onclick="removeImage(${i})">✕</button>`;
    imgPreviews.appendChild(chip);
  });
}
function removeImage(i) { uploadedImages.splice(i, 1); renderImagePreviews(); updateSendBtn(); }

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  CHAT — Mode Toggle
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function setMode(mode) {
  currentMode = mode;
  const fast = document.getElementById('modeFast');
  const deep = document.getElementById('modeDeep');
  const slider = document.getElementById('modeSlider');
  if (!fast) return;
  if (mode === 'fast') {
    fast.classList.add('active'); deep.classList.remove('active');
    slider.style.width = fast.offsetWidth + 'px'; slider.style.transform = 'translateX(0)';
  } else {
    deep.classList.add('active'); fast.classList.remove('active');
    slider.style.width = deep.offsetWidth + 'px';
    slider.style.transform = `translateX(${fast.offsetWidth}px)`;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const fast = document.getElementById('modeFast');
  const slider = document.getElementById('modeSlider');
  if (fast && slider) slider.style.width = fast.offsetWidth + 'px';

  // Restore language toggle
  if (currentLanguage === 'English') setLanguage('English');
  updateUILanguage();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  CHAT — Send Message (Ollama via Flask)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const chatMessages = document.getElementById('chatMessages');

async function sendMessage() {
  if (!textarea || !chatMessages) return;
  const text = textarea.value.trim();
  const images = [...uploadedImages];
  if (!text && images.length === 0) return;

  appendMessage('user', text, images);

  textarea.value = ''; textarea.style.height = 'auto';
  uploadedImages = []; renderImagePreviews(); updateSendBtn();

  chatHistory.push({ role: 'user', content: text });

  const base64Images = images.length > 0
    ? images.map(img => img.data.replace(/^data:image\/[a-z]+;base64,/, ''))
    : null;

  showTyping();

  // Auto-create a conversation on first message (only if save is on)
  const studentId = parseInt(localStorage.getItem('prajna_student_id')) || null;
  if (saveChatsEnabled && studentId && !currentConversationId) {
    try {
      const cRes = await fetch('/api/conversations', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({student_id: studentId})
      });
      const cData = await cRes.json();
      currentConversationId = cData.conversation_id;
    } catch(e) {}
  }

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history: chatHistory.slice(-20),
        images: base64Images,
        mode: currentMode,
        language: currentLanguage,
        student_id: studentId,
        conversation_id: saveChatsEnabled ? currentConversationId : null,
      }),
    });

    hideTyping();
    if (!res.ok) { appendMessage('bot', t('⚠️ Server error. Check if Ollama is running.', '⚠️ सर्वर त्रुटि। Ollama चल रहा है या नहीं जांचें।')); return; }

    const data = await res.json();
    const action = data.action || 'explain';
    const reply = data.tutor_response || data.error || 'No response received.';

    chatHistory.push({ role: 'assistant', content: reply });

    // Refresh conversation list so auto-title appears immediately
    if (saveChatsEnabled && studentId) loadConversations(studentId);


    appendMessage('bot', reply);

    // Quiz card
    if (data.quiz_data && (action === 'quiz' || action === 'game')) {
      appendQuiz(data.quiz_data, data.topic);
    }

  } catch (err) {
    hideTyping();
    appendMessage('bot', t('⚠️ Cannot reach the server.', '⚠️ सर्वर से कनेक्ट नहीं हो पा रहा।'));
  }
}

// ─── Render message ───
function appendMessage(type, text, images, badge) {
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const msgDiv = document.createElement('div');
  msgDiv.className = `msg msg--${type}`;

  let imgsHtml = '';
  if (images && images.length) {
    imgsHtml = images.map(img => `<img src="${img.data}" class="msg-img" alt="attached">`).join('');
  }

  const badgeHtml = '';
  const ttsHtml = type === 'bot' ? `<button class="tts-btn" onclick="speak(this.closest('.msg').querySelector('.msg-bubble').textContent)">${t('🔊 Listen', '🔊 सुनो')}</button>` : '';

  if (type === 'user') {
    msgDiv.innerHTML = `<div>${imgsHtml}<div class="msg-bubble">${escapeHtml(text)}</div><div class="msg-time" style="text-align:right;">${time}</div></div>`;
  } else {
    msgDiv.innerHTML = `<div class="msg-avatar">प्र</div><div>${imgsHtml}${badgeHtml}<div class="msg-bubble">${formatResponse(text)}</div>${ttsHtml}<div class="msg-time">${time}</div></div>`;
  }

  chatMessages.appendChild(msgDiv);
  msgDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// ─── Quiz card ───
function appendQuiz(quiz, topic) {
  if (!quiz || !quiz.question) return;
  const quizDiv = document.createElement('div');
  quizDiv.className = 'msg msg--bot';

  const optsHtml = (quiz.options || []).map((opt, i) => {
    const letter = String.fromCharCode(65 + i);
    return `<button class="quiz-option" data-correct="${opt === quiz.correct_answer}" onclick="checkAnswer(this, '${escapeAttr(quiz.correct_answer)}', '${escapeAttr(quiz.explanation || '')}', '${escapeAttr(topic || '')}', '${escapeAttr(quiz.quiz_type || 'mcq')}', '${escapeAttr(quiz.question || '')}')">
      <span class="quiz-letter">${letter}</span> ${escapeHtml(opt)}
    </button>`;
  }).join('');

  quizDiv.innerHTML = `<div class="msg-avatar">प्र</div><div><div class="msg-bubble quiz-card">
    <div class="quiz-type">${quiz.quiz_type || 'quiz'}</div>
    <div class="quiz-question">${escapeHtml(quiz.question)}</div>
    <div class="quiz-options">${optsHtml}</div>
    <div class="quiz-feedback" style="display:none;"></div>
  </div></div>`;

  chatMessages.appendChild(quizDiv);
  quizDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function checkAnswer(btn, correct, explanation, topic, quizType, question) {
  const card = btn.closest('.quiz-card');
  const buttons = card.querySelectorAll('.quiz-option');
  const feedback = card.querySelector('.quiz-feedback');
  const letter = btn.querySelector('.quiz-letter');
  const selected = btn.textContent.replace(letter ? letter.textContent : '', '').trim(); // Strip letter badge properly

  buttons.forEach(b => { b.disabled = true; if (b.dataset.correct === 'true') b.classList.add('correct'); });

  const isCorrect = btn.dataset.correct === 'true';
  if (isCorrect) {
    btn.classList.add('correct');
    feedback.textContent = t('✅ Correct! ', '✅ सही! ') + explanation;
    feedback.style.color = '#22c55e';
  } else {
    btn.classList.add('wrong');
    feedback.textContent = t('❌ Wrong. ', '❌ गलत। ') + explanation;
    feedback.style.color = '#ef4444';
  }
  feedback.style.display = 'block';

  // Log quiz result to backend
  const studentId = localStorage.getItem('prajna_student_id');
  if (studentId) {
    fetch('/api/quiz-result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: parseInt(studentId),
        topic: topic,
        quiz_type: quizType,
        question: question,
        student_answer: selected,
        correct_answer: correct,
        is_correct: isCorrect,
      }),
    }).catch(() => {});
  }
}

// ─── TTS ───
function speak(text) {
  if (!('speechSynthesis' in window)) { showToast(t('TTS not supported', 'TTS सपोर्ट नहीं है')); return; }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = currentLanguage === 'English' ? 'en-IN' : 'hi-IN';
  window.speechSynthesis.speak(utterance);
}

// ─── Typing indicator ───
function showTyping() {
  if (!chatMessages) return;
  const el = document.createElement('div');
  el.className = 'msg msg--bot'; el.id = 'typingIndicator';
  el.innerHTML = `<div class="msg-avatar">प्र</div><div><div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div></div>`;
  chatMessages.appendChild(el);
  el.scrollIntoView({ behavior: 'smooth', block: 'end' });
}
function hideTyping() { const el = document.getElementById('typingIndicator'); if (el) el.remove(); }

// ─── Utilities ───
function escapeHtml(str) { if (!str) return ''; const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
function escapeAttr(str) { return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
function formatResponse(text) {
  return escapeHtml(text).replace(/\n/g, '<br>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}
