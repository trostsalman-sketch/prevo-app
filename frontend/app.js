const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// ВАЖНО: Замени на URL твоего API с Render после деплоя
const API = 'https://твой-бэкенд.onrender.com';

let currentUser = null;
let currentPage = 'home';

async function api(path, options = {}) {
    const opts = { ...options };
    if (!opts.headers) opts.headers = {};
    opts.headers['Authorization'] = `tma ${tg.initData}`;
    
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(opts.body);
    }
    
    const res = await fetch(`${API}${path}`, opts);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

function toast(msg) {
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2500);
}

async function init() {
    try {
        const data = await api('/api/auth');
        currentUser = { ...data.user, role: data.role };
        if (new URLSearchParams(location.search).get('admin') === '1') {
            if (currentUser.role === 'admin' || currentUser.role === 'creator') {
                showPage('admin');
            } else {
                showPage('home');
                toast('Доступ запрещен');
            }
        } else {
            showPage('home');
        }
    } catch (e) {
        toast('Ошибка авторизации');
    }
}

function showPage(page) {
    currentPage = page;
    document.querySelectorAll('.nav-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.page === page);
    });
    
    const app = document.getElementById('app');
    switch(page) {
        case 'home': renderHome(app); break;
        case 'character': renderCharacter(app); break;
        case 'social': renderSocial(app); break;
        case 'report': renderReport(app); break;
        case 'market': renderMarket(app); break;
        case 'irp': renderIRP(app); break;
        case 'admin': renderAdmin(app); break;
    }
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        if (btn.dataset.page === 'admin' && currentUser?.role === 'user') {
            toast('Доступ запрещен');
            return;
        }
        showPage(btn.dataset.page);
    });
});

function renderHome(app) {
    app.innerHTML = `
        <div class="header">
            <h1>PROJECT EVOLUTION</h1>
            <p>Премиум Telegram сообщество</p>
        </div>
        <div class="card">
            <h3 style="color: var(--gold); margin-bottom: 12px;">Добро пожаловать</h3>
            <p style="color: var(--text-secondary); line-height: 1.6;">
                Платформа для регистрации персонажей, общения и взаимодействия внутри проекта.
            </p>
        </div>
        <div class="card">
            <h3 style="color: var(--gold); margin-bottom: 12px;">Разделы</h3>
            <p style="color: var(--text-secondary); line-height: 1.8;">
                Персонаж — регистрация анкеты<br>
                Соцсеть — публикации и общение<br>
                Жалоба — сообщить о нарушении<br>
                Рынок — объявления<br>
                IRP — список нарушителей
            </p>
        </div>
    `;
}

function renderCharacter(app) {
    app.innerHTML = `
        <div class="header">
            <h1>Регистрация персонажа</h1>
            <p>Заполните анкету для участия</p>
        </div>
        <div class="card">
            <form id="charForm">
                <div class="form-group">
                    <label>Фотография персонажа</label>
                    <div class="photo-upload" onclick="document.getElementById('charPhoto').click()">
                        <div id="charPhotoLabel">Нажмите для загрузки</div>
                        <input type="file" id="charPhoto" accept="image/*" required>
                        <img id="charPreview" class="photo-preview" style="display:none">
                    </div>
                </div>
                <div class="form-group">
                    <label>Имя персонажа</label>
                    <input type="text" id="charName" required>
                </div>
                <div class="form-group">
                    <label>Возраст</label>
                    <input type="number" id="charAge" min="16" max="100" required>
                </div>
                <div class="form-group">
                    <label>Рост (см)</label>
                    <input type="number" id="charHeight" min="100" max="250" required>
                </div>
                <div class="form-group">
                    <label>Вес (кг)</label>
                    <input type="number" id="charWeight" min="30" max="200" required>
                </div>
                <div class="form-group">
                    <label>Биография</label>
                    <textarea id="charBio" required></textarea>
                </div>
                <button type="submit" class="btn">Отправить на модерацию</button>
            </form>
        </div>
    `;
    
    document.getElementById('charPhoto').onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => {
                document.getElementById('charPreview').src = ev.target.result;
                document.getElementById('charPreview').style.display = 'block';
                document.getElementById('charPhotoLabel').textContent = file.name;
            };
            reader.readAsDataURL(file);
        }
    };
    
    document.getElementById('charForm').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('photo', document.getElementById('charPhoto').files[0]);
        formData.append('name', document.getElementById('charName').value);
        formData.append('age', document.getElementById('charAge').value);
        formData.append('height', document.getElementById('charHeight').value);
        formData.append('weight', document.getElementById('charWeight').value);
        formData.append('bio', document.getElementById('charBio').value);
        
        try {
            await api('/api/character', { method: 'POST', body: formData, headers: {} });
            toast('Анкета отправлена');
            e.target.reset();
            document.getElementById('charPreview').style.display = 'none';
            document.getElementById('charPhotoLabel').textContent = 'Нажмите для загрузки';
        } catch (err) {
            toast('Ошибка отправки');
        }
    };
}

async function renderSocial(app) {
    app.innerHTML = `
        <div class="header">
            <h1>Соцсеть</h1>
            <p>Публикации и общение</p>
        </div>
        <div class="card">
            <button class="btn" onclick="showCreatePost()">Создать публикацию</button>
        </div>
        <div id="postsFeed"></div>
    `;
    loadPosts();
}

async function loadPosts() {
    try {
        const posts = await api('/api/posts');
        const feed = document.getElementById('postsFeed');
        feed.innerHTML = posts.map(post => `
            <div class="post">
                <div class="post-header">
                    <div class="post-avatar">${(post.first_name || 'U')[0].toUpperCase()}</div>
                    <div>
                        <div class="post-author">${post.first_name || 'User'}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">@${post.username || ''}</div>
                    </div>
                </div>
                ${post.photo ? `<img class="post-image" src="${API}/${post.photo}">` : ''}
                <div class="post-content">
                    <p style="margin-bottom: 8px;">${post.description}</p>
                    ${post.hashtags ? `<div class="hashtag">${post.hashtags}</div>` : ''}
                </div>
                <div class="post-actions">
                    <button class="action-btn" onclick="likePost(${post.id})">${post.likes_count} лайков</button>
                    <button class="action-btn" onclick="showComments(${post.id})">${post.comments_count} комментариев</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        toast('Ошибка загрузки');
    }
}

async function likePost(id) {
    await api(`/api/post/${id}/like`, { method: 'POST', body: {} });
    loadPosts();
}

async function showComments(postId) {
    const comments = await api(`/api/post/${postId}/comments`);
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <h3 style="color: var(--gold); margin-bottom: 16px;">Комментарии</h3>
            <div style="max-height: 300px; overflow-y: auto; margin-bottom: 16px;">
                ${comments.map(c => `
                    <div style="padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <div style="font-weight: 600; color: var(--gold); font-size: 13px;">${c.first_name || 'User'}</div>
                        <div style="font-size: 14px; margin-top: 4px;">${c.text}</div>
                    </div>
                `).join('') || '<p style="color: var(--text-secondary);">Нет комментариев</p>'}
            </div>
            <form id="commentForm">
                <textarea id="commentText" placeholder="Ваш комментарий" style="width:100%;padding:10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;color:white;"></textarea>
                <button type="submit" class="btn" style="margin-top:12px;">Отправить</button>
            </form>
            <button class="btn btn-secondary" style="margin-top: 8px;" onclick="this.closest('.modal').remove()">Закрыть</button>
        </div>
    `;
    document.body.appendChild(modal);
    
    document.getElementById('commentForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData();
        fd.append('text', document.getElementById('commentText').value);
        await api(`/api/post/${postId}/comment`, { method: 'POST', body: fd, headers: {} });
        modal.remove();
        showComments(postId);
    };
}

function showCreatePost() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <h3 style="color: var(--gold); margin-bottom: 16px;">Новая публикация</h3>
            <form id="postForm">
                <div class="photo-upload" onclick="document.getElementById('postPhoto').click()" style="margin-bottom: 16px;">
                    <div id="postPhotoLabel">Добавить фото</div>
                    <input type="file" id="postPhoto" accept="image/*">
                </div>
                <textarea id="postDesc" placeholder="Описание" required style="width:100%;padding:10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;color:white;min-height:80px;"></textarea>
                <input id="postTags" placeholder="#хештеги" style="width:100%;padding:10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;color:white;margin-top:10px;">
                <button type="submit" class="btn" style="margin-top: 16px;">Опубликовать</button>
            </form>
            <button class="btn btn-secondary" style="margin-top: 8px;" onclick="this.closest('.modal').remove()">Отмена</button>
        </div>
    `;
    document.body.appendChild(modal);
    
    document.getElementById('postForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData();
        const photoFile = document.getElementById('postPhoto').files[0];
        if (photoFile) fd.append('photo', photoFile);
        fd.append('description', document.getElementById('postDesc').value);
        fd.append('hashtags', document.getElementById('postTags').value);
        
        await api('/api/post', { method: 'POST', body: fd, headers: {} });
        modal.remove();
        toast('Опубликовано');
        loadPosts();
    };
}

function renderReport(app) {
    app.innerHTML = `
        <div class="header">
            <h1>Жалоба</h1>
            <p>Сообщить о нарушении</p>
        </div>
        <div class="card">
            <form id="reportForm">
                <div class="form-group">
                    <label>Ваш никнейм</label>
                    <input type="text" id="repReporter" value="@${currentUser?.username || ''}" required>
                </div>
                <div class="form-group">
                    <label>Никнейм нарушителя</label>
                    <input type="text" id="repViolator" placeholder="@username" required>
                </div>
                <div class="form-group">
                    <label>Причина</label>
                    <textarea id="repReason" required></textarea>
                </div>
                <div class="form-group">
                    <label>Доказательства</label>
                    <div class="photo-upload" onclick="document.getElementById('repEvidence').click()">
                        <div id="repEvidenceLabel">Прикрепить фото</div>
                        <input type="file" id="repEvidence" accept="image/*">
                    </div>
                </div>
                <button type="submit" class="btn">Отправить жалобу</button>
            </form>
        </div>
    `;
    
    document.getElementById('repEvidence').onchange = (e) => {
        document.getElementById('repEvidenceLabel').textContent = e.target.files[0]?.name || 'Прикрепить фото';
    };
    
    document.getElementById('reportForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData();
        fd.append('reporter', document.getElementById('repReporter').value);
        fd.append('violator', document.getElementById('repViolator').value);
        fd.append('reason', document.getElementById('repReason').value);
        const file = document.getElementById('repEvidence').files[0];
        if (file) fd.append('evidence', file);
        
        await api('/api/report', { method: 'POST', body: fd, headers: {} });
        toast('Жалоба отправлена');
        e.target.reset();
    };
}

function renderMarket(app) {
    app.innerHTML = `
        <div class="header">
            <h1>Черный рынок</h1>
            <p>Товары и услуги</p>
        </div>
        <div class="card">
            <button class="btn" onclick="showCreateMarket()">Выставить товар</button>
        </div>
        <div id="marketFeed"></div>
    `;
    loadMarket();
}

async function loadMarket() {
    try {
        const items = await api('/api/market');
        document.getElementById('marketFeed').innerHTML = items.map(item => `
            <div class="market-item">
                <img class="market-image" src="${API}/${item.photo}">
                <div class="market-content">
                    <p style="margin-bottom: 12px;">${item.description}</p>
                    <div class="market-contact">${item.contact}</div>
                </div>
            </div>
        `).join('') || '<div class="card"><p style="color: var(--text-secondary); text-align: center;">Нет объявлений</p></div>';
    } catch (e) {
        toast('Ошибка загрузки');
    }
}

function showCreateMarket() {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <h3 style="color: var(--gold); margin-bottom: 16px;">Новое объявление</h3>
            <form id="marketForm">
                <div class="photo-upload" onclick="document.getElementById('marketPhoto').click()" style="margin-bottom: 16px;">
                    <div id="marketPhotoLabel">Фото товара</div>
                    <input type="file" id="marketPhoto" accept="image/*" required>
                </div>
                <textarea id="marketDesc" placeholder="Описание" required style="width:100%;padding:10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;color:white;min-height:80px;"></textarea>
                <input id="marketContact" placeholder="@username" required style="width:100%;padding:10px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;color:white;margin-top:10px;">
                <button type="submit" class="btn" style="margin-top: 16px;">Выставить товар</button>
            </form>
            <button class="btn btn-secondary" style="margin-top: 8px;" onclick="this.closest('.modal').remove()">Отмена</button>
        </div>
    `;
    document.body.appendChild(modal);
    
    document.getElementById('marketForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData();
        fd.append('photo', document.getElementById('marketPhoto').files[0]);
        fd.append('description', document.getElementById('marketDesc').value);
        fd.append('contact', document.getElementById('marketContact').value);
        
        await fetch(`${API}/api/market`, { method: 'POST', body: fd });
        modal.remove();
        toast('Товар выставлен');
        loadMarket();
    };
}

async function renderIRP(app) {
    app.innerHTML = `
        <div class="header">
            <h1>IRP лист</h1>
            <p>Одобренные жалобы</p>
        </div>
        <div id="irpFeed"></div>
    `;
    try {
        const items = await api('/api/irp');
        document.getElementById('irpFeed').innerHTML = items.length ? items.map(item => `
            <div class="card">
                <h3 style="color: var(--gold); margin-bottom: 8px;">${item.violator}</h3>
                <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 12px;">Заявитель: ${item.reporter}</p>
                <p style="line-height: 1.6;">${item.reason}</p>
                ${item.evidence ? `<img src="${API}/${item.evidence}" style="width:100%;border-radius:10px;margin-top:12px;">` : ''}
            </div>
        `).join('') : '<div class="card"><p style="text-align:center;color:var(--text-secondary);">Список пуст</p></div>';
    } catch (e) {
        toast('Ошибка');
    }
}

async function renderAdmin(app) {
    app.innerHTML = `
        <div class="header">
            <h1>Админ-панель</h1>
            <p>Управление проектом</p>
        </div>
        <div class="card">
            <button class="btn btn-secondary" onclick="showAdminTab('characters')">Анкеты</button>
            <button class="btn btn-secondary" style="margin-top:8px;" onclick="showAdminTab('reports')">Жалобы</button>
            <button class="btn btn-secondary" style="margin-top:8px;" onclick="showAdminTab('stats')">Статистика</button>
        </div>
        <div id="adminContent"></div>
    `;
    showAdminTab('characters');
}

async function showAdminTab(tab) {
    const content = document.getElementById('adminContent');
    if (tab === 'stats') {
        const stats = await api('/api/admin/stats');
        content.innerHTML = `
            <div class="card">
                <h3 style="color: var(--gold); margin-bottom: 16px;">Статистика проекта</h3>
                <p>Пользователей: <strong>${stats.users}</strong></p>
                <p>Анкет на модерации: <strong>${stats.characters_pending}</strong></p>
                <p>Одобренных анкет: <strong>${stats.characters_approved}</strong></p>
                <p>Публикаций: <strong>${stats.posts}</strong></p>
                <p>Жалоб на модерации: <strong>${stats.reports_pending}</strong></p>
                <p>Одобренных жалоб: <strong>${stats.reports_approved}</strong></p>
                <p>Товаров на рынке: <strong>${stats.market_items}</strong></p>
                <p>Администраторов: <strong>${stats.admins}</strong></p>
            </div>
        `;
        return;
    }
    
    if (tab === 'characters') {
        const chars = await api('/api/admin/characters');
        content.innerHTML = chars.length ? chars.map(c => `
            <div class="card">
                <img src="${API}/${c.photo}" style="width:100%;border-radius:10px;margin-bottom:12px;">
                <h3 style="color: var(--gold);">${c.name}</h3>
                <p style="color: var(--text-secondary); font-size: 13px;">Возраст: ${c.age} | Рост: ${c.height}см | Вес: ${c.weight}кг</p>
                <p style="margin-top: 8px; line-height: 1.6;">${c.bio}</p>
                <button class="btn" style="margin-top: 12px;" onclick="approveChar(${c.id})">Принять</button>
                <button class="btn btn-secondary" style="margin-top: 8px;" onclick="rejectChar(${c.id})">Отклонить</button>
            </div>
        `).join('') : '<div class="card"><p style="text-align:center;color:var(--text-secondary);">Нет анкет</p></div>';
        return;
    }
    
    if (tab === 'reports') {
        const reports = await api('/api/admin/reports');
        content.innerHTML = reports.length ? reports.map(r => `
            <div class="card">
                <p style="color: var(--text-secondary); font-size: 13px;">Нарушитель: <strong style="color:var(--gold);">${r.violator}</strong></p>
                <p style="margin-top: 8px;">${r.reason}</p>
                ${r.evidence ? `<img src="${API}/${r.evidence}" style="width:100%;border-radius:10px;margin-top:12px;">` : ''}
                <button class="btn" style="margin-top: 12px;" onclick="approveReport(${r.id})">Принять</button>
                <button class="btn btn-secondary" style="margin-top: 8px;" onclick="rejectReport(${r.id})">Отклонить</button>
            </div>
        `).join('') : '<div class="card"><p style="text-align:center;color:var(--text-secondary);">Нет жалоб</p></div>';
    }
}

async function approveChar(id) {
    await api(`/api/admin/character/${id}/approve`, { method: 'POST', body: {} });
    toast('Анкета одобрена');
    showAdminTab('characters');
}

async function rejectChar(id) {
    const reason = prompt('Причина отклонения:');
    if (!reason) return;
    const fd = new FormData();
    fd.append('reason', reason);
    await api(`/api/admin/character/${id}/reject`, { method: 'POST', body: fd, headers: {} });
    toast('Анкета отклонена');
    showAdminTab('characters');
}

async function approveReport(id) {
    await api(`/api/admin/report/${id}/approve`, { method: 'POST', body: {} });
    toast('Жалоба одобрена');
    showAdminTab('reports');
}

async function rejectReport(id) {
    const reason = prompt('Причина отклонения:');
    if (!reason) return;
    const fd = new FormData();
    fd.append('reason', reason);
    await api(`/api/admin/report/${id}/reject`, { method: 'POST', body: fd, headers: {} });
    toast('Жалоба отклонена');
    showAdminTab('reports');
}

init();
