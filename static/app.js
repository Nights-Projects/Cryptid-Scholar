const API_BASE = '';
let CRYPTIDS = [];
let cryptidsLoaded = false;

function getThumbUrl(cryptid) {
    if (!cryptid || cryptid.id == null) return '/static/placeholder.jpg';
    return '/static/thumbs/' + encodeURIComponent(cryptid.id + '.jpg');
}

function getCryptidImage(cryptid) {
    const initial = cryptid.name.charAt(0).toUpperCase();
    const typeColor = {
        'aquatic': '#2196F3',
        'terrestrial': '#e74c3c',
        'flying': '#9b59b6'
    };
    const color = typeColor[cryptid.type] || '#555';
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200"><rect width="300" height="200" fill="#1a002f"/><text x="150" y="105" font-family="sans-serif" font-size="60" fill="' + color + '" text-anchor="middle">' + initial + '</text></svg>';
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
}

function typeBadge(cryptid) {
    const t = cryptid.type || 'terrestrial';
    return '<span class="type-badge type-' + t + '">' + t + '</span>';
}

async function loadCryptids() {
    const loading = document.getElementById('browseLoading');
    loading.style.display = 'block';

    try {
        const resp = await fetch('/api/cryptids/all');
        if (!resp.ok) throw new Error('Failed to load cryptids');
        const data = await resp.json();
        CRYPTIDS = data.cryptids;
        cryptidsLoaded = true;
        document.getElementById('appSubtitle').textContent = 'Learn every world cryptid — ' + CRYPTIDS.length + ' cryptids worldwide';
        init();
    } catch (e) {
        console.error('Load error:', e);
        document.getElementById('appSubtitle').textContent = 'Error loading cryptids. Please refresh.';
        document.getElementById('cryptidGrid').innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">Could not load cryptid data. Check your connection.</div></div>';
    } finally {
        loading.style.display = 'none';
    }
}

let filteredCryptids = [];
let currentFilter = 'all';
let searchQuery = '';
let fcIndex = 0;
let fcOrder = [];
let quizState = { score: 0, total: 0, current: null };
let learnedSet = new Set();

function renderBrowse() {
    const grid = document.getElementById('cryptidGrid');
    const empty = document.getElementById('emptyState');
    const stats = document.getElementById('browseStats');

    filteredCryptids = CRYPTIDS.filter(c => {
        const matchFilter = currentFilter === 'all' || (c.type || 'terrestrial') === currentFilter;
        const matchSearch = !searchQuery ||
            c.name.toLowerCase().includes(searchQuery) ||
            (c.location && c.location.toLowerCase().includes(searchQuery)) ||
            (c.country && c.country.toLowerCase().includes(searchQuery)) ||
            (c.other_names && c.other_names.toLowerCase().includes(searchQuery));
        return matchFilter && matchSearch;
    });

    const counts = { aquatic: 0, terrestrial: 0, flying: 0 };
    CRYPTIDS.forEach(c => {
        const t = c.type || 'terrestrial';
        if (counts[t] !== undefined) counts[t]++;
    });
    stats.innerHTML =
        '<div class="stat-item s1"><div class="stat-value">' + counts.aquatic + '</div><div class="stat-label">Aquatic</div></div>' +
        '<div class="stat-item s2"><div class="stat-value">' + counts.terrestrial + '</div><div class="stat-label">Terrestrial</div></div>' +
        '<div class="stat-item s3"><div class="stat-value">' + counts.flying + '</div><div class="stat-label">Flying</div></div>' +
        '<div class="stat-item s4"><div class="stat-value">' + CRYPTIDS.length + '</div><div class="stat-label">Total</div></div>';

    if (filteredCryptids.length === 0) {
        grid.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    grid.style.display = 'grid';
    empty.style.display = 'none';

    grid.innerHTML = filteredCryptids.map(cryptid => {
        const t = cryptid.type || 'terrestrial';
        const badge = typeBadge(cryptid);
        const imgSrc = getThumbUrl(cryptid);
        const location = cryptid.location || 'Unknown';
        const country = cryptid.country || '';
        return '<div class="cryptid-card" data-id="' + cryptid.id + '">' +
            '<img class="cryptid-img" src="' + imgSrc + '" alt="' + cryptid.name + '" loading="lazy" onerror="this.outerHTML=\'<div class=\\"cryptid-img-placeholder\\">👻</div>\'">' +
            '<div class="cryptid-info"><div class="cryptid-name">' + cryptid.name + '</div><div class="cryptid-meta">' +
            badge +
            '<span class="cryptid-location">' + location + '</span>' +
            (country ? '<span class="cryptid-country">' + country + '</span>' : '') +
            '</div></div></div>';
    }).join('');

    grid.querySelectorAll('.cryptid-card').forEach(card => {
        card.addEventListener('click', () => {
            const id = parseInt(card.dataset.id);
            const cryptid = CRYPTIDS.find(c => c.id === id);
            if (cryptid) openDetail(cryptid);
        });
    });
}

function openDetail(cryptid) {
    const modal = document.getElementById('detailModal');
    const imgEl = document.getElementById('modalImg');
    if (cryptid.image_url) {
        imgEl.src = cryptid.image_url;
    } else {
        imgEl.src = getThumbUrl(cryptid);
    }
    imgEl.onerror = () => { imgEl.src = getCryptidImage(cryptid); };

    document.getElementById('modalTitle').textContent = cryptid.name;
    document.getElementById('modalSubtitle').textContent =
        (cryptid.type || 'terrestrial') + ' • ' + (cryptid.location || 'Unknown location');
    document.getElementById('modalFact').textContent = cryptid.fact || 'No additional information available.';
    document.getElementById('modalTips').textContent = cryptid.tips || 'Study the creature\'s distinctive features: habitat, size, and reported behavior.';
    document.getElementById('modalOtherNames').textContent = cryptid.other_names || 'No known aliases.';
    document.getElementById('modalDescription').textContent = cryptid.description || 'No detailed description available.';

    const meta = document.getElementById('modalMeta');
    const items = [];
    if (cryptid.country) items.push('<div class="meta-item"><div class="meta-value">' + cryptid.country + '</div><div class="meta-label">Country</div></div>');
    if (cryptid.location) items.push('<div class="meta-item"><div class="meta-value">' + cryptid.location + '</div><div class="meta-label">Location</div></div>');
    const typeDisplay = (cryptid.type || 'terrestrial').charAt(0).toUpperCase() + (cryptid.type || 'terrestrial').slice(1);
    items.push('<div class="meta-item"><div class="meta-value">' + typeDisplay + '</div><div class="meta-label">Type</div></div>');
    if (cryptid.registries) items.push('<div class="meta-item"><div class="meta-value">' + cryptid.registries.toUpperCase() + '</div><div class="meta-label">Registry</div></div>');
    meta.innerHTML = items.join('');

    modal.classList.add('open');
    learnedSet.add(cryptid.id);
    saveProgress();
}

document.getElementById('modalClose').addEventListener('click', () => {
    document.getElementById('detailModal').classList.remove('open');
});
document.getElementById('detailModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) document.getElementById('detailModal').classList.remove('open');
});

function initFlashcards() {
    if (fcOrder.length !== filteredCryptids.length) {
        fcOrder = filteredCryptids.map((_, i) => i);
        shuffleArray(fcOrder);
    }
    fcIndex = Math.min(fcIndex, fcOrder.length - 1);
    if (fcIndex < 0) fcIndex = 0;
    renderFlashcard();
}

function renderFlashcard() {
    if (fcOrder.length === 0) return;
    const idx = fcOrder[fcIndex];
    const cryptid = filteredCryptids[idx];
    if (!cryptid) return;

    const imgEl = document.getElementById('fcImg');
    if (cryptid.image_url) {
        imgEl.src = cryptid.image_url;
    } else {
        imgEl.src = getThumbUrl(cryptid);
    }
    imgEl.onerror = () => { imgEl.src = getCryptidImage(cryptid); };

    document.getElementById('fcName').textContent = cryptid.name;
    document.getElementById('fcNameBack').textContent = cryptid.name;
    document.getElementById('fcType').textContent = (cryptid.type || 'terrestrial').toUpperCase();
    document.getElementById('fcHint').textContent =
        (cryptid.country || 'Unknown origin') + ' • ' + (cryptid.location || 'Unknown location');

    document.getElementById('flashcard').classList.remove('flipped');
}

document.getElementById('flashcardContainer').addEventListener('click', () => {
    document.getElementById('flashcard').classList.toggle('flipped');
});
document.getElementById('fcNext').addEventListener('click', () => {
    fcIndex = (fcIndex + 1) % fcOrder.length;
    renderFlashcard();
});
document.getElementById('fcPrev').addEventListener('click', () => {
    fcIndex = (fcIndex - 1 + fcOrder.length) % fcOrder.length;
    renderFlashcard();
});
document.getElementById('fcShuffle').addEventListener('click', () => {
    fcOrder = filteredCryptids.map((_, i) => i);
    shuffleArray(fcOrder);
    fcIndex = 0;
    renderFlashcard();
});

function generateQuizQuestion() {
    if (filteredCryptids.length < 2) return;
    const correct = filteredCryptids[Math.floor(Math.random() * filteredCryptids.length)];
    const options = [correct];
    const pool = filteredCryptids.filter(b => b.id !== correct.id);
    shuffleArray(pool);
    for (let i = 0; i < Math.min(3, pool.length); i++) options.push(pool[i]);
    shuffleArray(options);

    quizState.current = { correct, options };

    const imgEl = document.getElementById('quizImg');
    if (correct.image_url) {
        imgEl.src = correct.image_url;
    } else {
        imgEl.src = getThumbUrl(correct);
    }
    imgEl.onerror = () => { imgEl.src = getCryptidImage(correct); };

    const optsEl = document.getElementById('quizOptions');
    optsEl.innerHTML = options.map((opt, i) =>
        '<button class="quiz-option" data-idx="' + i + '" data-id="' + opt.id + '">' + opt.name + '</button>'
    ).join('');

    optsEl.querySelectorAll('.quiz-option').forEach(btn => {
        btn.addEventListener('click', () => handleQuizAnswer(btn));
    });
}

function handleQuizAnswer(btn) {
    const selectedId = parseInt(btn.dataset.id);
    const correctId = quizState.current.correct.id;
    quizState.total++;

    const allBtns = document.querySelectorAll('.quiz-option');
    allBtns.forEach(b => {
        b.disabled = true;
        if (parseInt(b.dataset.id) === correctId) b.classList.add('correct');
    });

    if (selectedId === correctId) {
        quizState.score++;
        btn.classList.add('correct');
    } else {
        btn.classList.add('wrong');
    }

    document.getElementById('quizScore').textContent = quizState.score + ' / ' + quizState.total;
    learnedSet.add(quizState.current.correct.id);
    saveProgress();
}

document.getElementById('quizNext').addEventListener('click', generateQuizQuestion);

function renderStats() {
    const counts = { aquatic: 0, terrestrial: 0, flying: 0 };
    CRYPTIDS.forEach(c => {
        const t = c.type || 'terrestrial';
        if (counts[t] !== undefined) counts[t]++;
    });
    document.getElementById('statsBar').innerHTML =
        '<div class="stat-item s1"><div class="stat-value">' + counts.aquatic + '</div><div class="stat-label">Aquatic</div></div>' +
        '<div class="stat-item s2"><div class="stat-value">' + counts.terrestrial + '</div><div class="stat-label">Terrestrial</div></div>' +
        '<div class="stat-item s3"><div class="stat-value">' + counts.flying + '</div><div class="stat-label">Flying</div></div>' +
        '<div class="stat-item s4"><div class="stat-value">' + CRYPTIDS.length + '</div><div class="stat-label">Total</div></div>';

    const countryCounts = {};
    CRYPTIDS.forEach(c => {
        if (c.country) {
            countryCounts[c.country] = (countryCounts[c.country] || 0) + 1;
        }
    });
    const topCountries = Object.entries(countryCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    document.getElementById('topCountries').innerHTML = topCountries.map(([country, count]) =>
        '<div style="padding:4px 0;border-bottom:1px solid var(--border);"><span style="color:var(--gold);font-weight:bold;">' + count + '</span> <span style="color:var(--text);font-weight:600;">' + country + '</span></div>'
    ).join('');

    const learned = learnedSet.size;
    const total = CRYPTIDS.length;
    const pct = total > 0 ? Math.round((learned / total) * 100) : 0;
    document.getElementById('progressContent').innerHTML =
        '<p style="margin-bottom:8px;">You\'ve studied <strong style="color:var(--gold);">' + learned + '</strong> of <strong style="color:var(--text);">' + total + '</strong> cryptids (' + pct + '%)</p>' +
        '<div style="background:var(--card-2);border-radius:12px;height:16px;overflow:hidden;"><div style="background:var(--gold);height:100%;width:' + pct + '%;border-radius:12px;transition:width 0.5s;"></div></div>';
}

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

function saveProgress() {
    try { localStorage.setItem('cryptidScholar_learned', JSON.stringify([...learnedSet])); } catch(e) {}
}
function loadProgress() {
    try {
        const data = localStorage.getItem('cryptidScholar_learned');
        if (data) learnedSet = new Set(JSON.parse(data));
    } catch(e) {}
}

document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const mode = tab.dataset.tab;
        document.querySelectorAll('.mode').forEach(m => m.style.display = 'none');
        document.getElementById(mode + 'Mode').style.display = 'block';

        if (mode === 'browse') renderBrowse();
        if (mode === 'flashcard') { filteredCryptids = getActiveCryptids(); initFlashcards(); }
        if (mode === 'quiz') { filteredCryptids = getActiveCryptids(); generateQuizQuestion(); }
        if (mode === 'stats') renderStats();
    });
});

document.getElementById('searchInput').addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase();
    renderBrowse();
});

document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => {
            c.className = 'chip';
        });
        const filter = chip.dataset.filter;
        currentFilter = filter;
        if (filter === 'all') chip.classList.add('active-all');
        else chip.classList.add('active-' + filter);
        fcOrder = [];
        renderBrowse();
    });
});

function getActiveCryptids() {
    return CRYPTIDS.filter(c => {
        const matchFilter = currentFilter === 'all' || (c.type || 'terrestrial') === currentFilter;
        const matchSearch = !searchQuery || c.name.toLowerCase().includes(searchQuery);
        return matchFilter && matchSearch;
    });
}

function init() {
    loadProgress();
    renderBrowse();
    renderStats();
}

loadCryptids();
