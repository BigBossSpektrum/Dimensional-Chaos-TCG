document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('sendData');
    const hiddenSetCode = document.getElementById('setCodeHidden');
    const previewBox = document.getElementById('searchPreview');
    const overlay = document.getElementById('searchOverlay');
    if (!input || !previewBox || !hiddenSetCode || !overlay) return;

    let debounceTimer = null;
    let activeIndex = -1;
    let isSetCodeSelected = false;

    // Si ya hay un set_code seleccionado al cargar, mostrarlo como tag
    if (hiddenSetCode.value) {
        showSetCodeTag(hiddenSetCode.value);
    }

    input.addEventListener('input', function () {
        const term = input.value.trim();
        clearTimeout(debounceTimer);

        if (isSetCodeSelected) return;

        if (term.length < 3) {
            closePreview();
            return;
        }

        debounceTimer = setTimeout(function () {
            // Buscar cartas y set_codes en paralelo
            Promise.all([
                fetch('/api/suggest-cards/?term=' + encodeURIComponent(term)).then(function (r) { return r.json(); }),
                fetch('/api/suggest-set-codes/?term=' + encodeURIComponent(term)).then(function (r) { return r.json(); })
            ]).then(function (results) {
                renderPreview(results[0], results[1], term);
            }).catch(function () {
                closePreview();
            });
        }, 300);
    });

    input.addEventListener('keydown', function (e) {
        const items = previewBox.querySelectorAll('.preview-card-item, .preview-setcode-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, items.length - 1);
            updateActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, 0);
            updateActive(items);
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            items[activeIndex].click();
        } else if (e.key === 'Escape') {
            closePreview();
        }
    });

    document.addEventListener('click', function (e) {
        if (!input.contains(e.target) && !previewBox.contains(e.target)) {
            closePreview();
        }
    });

    // Cerrar al hacer clic en el overlay
    overlay.addEventListener('click', function () {
        closePreview();
        input.blur();
    });

    function renderPreview(cards, setCodes, term) {
        previewBox.innerHTML = '';
        activeIndex = -1;

        if (!cards.length && !setCodes.length) {
            closePreview();
            return;
        }

        // Posicionar debajo del input
        var inputRect = input.getBoundingClientRect();
        previewBox.style.top = (inputRect.bottom) + 'px';
        previewBox.style.left = (inputRect.left + inputRect.width / 2) + 'px';
        previewBox.style.width = inputRect.width + 'px';

        // Header: "Search for X in ..."
        var header = document.createElement('div');
        header.className = 'search-preview-header';
        header.innerHTML = 'Search for "<strong>' + escapeHtml(term) + '</strong>" in ...';
        previewBox.appendChild(header);

        // Sección de cartas - lista tipo TCGPlayer
        if (cards.length) {
            var title = document.createElement('div');
            title.className = 'search-preview-section-title';
            title.innerHTML = '<i class="fa-solid fa-clone"></i> in Yu-Gi-Oh!';
            previewBox.appendChild(title);

            cards.forEach(function (card) {
                var a = document.createElement('a');
                a.className = 'preview-card-item';
                a.href = '/card/' + card.card_id + '/';

                var nameSpan = document.createElement('div');
                nameSpan.className = 'preview-card-name';
                nameSpan.innerHTML = highlightMatch(card.name, term);

                var category = document.createElement('div');
                category.className = 'preview-card-category';
                category.textContent = 'in Yu-Gi-Oh!';

                a.appendChild(nameSpan);
                a.appendChild(category);

                a.addEventListener('click', function () {
                    closePreview();
                });

                previewBox.appendChild(a);
            });
        }

        // Sección de set codes
        if (setCodes.length) {
            var setTitle = document.createElement('div');
            setTitle.className = 'search-preview-section-title';
            setTitle.innerHTML = '<i class="fa-solid fa-box-open"></i> Set Codes';
            previewBox.appendChild(setTitle);

            setCodes.forEach(function (item) {
                var div = document.createElement('div');
                div.className = 'preview-setcode-item';
                div.innerHTML =
                    '<span class="set-code-label">' + highlightMatch(item.set_code, term) + '</span>' +
                    '<span class="set-name-label">' + escapeHtml(item.set_name) + '</span>';
                div.dataset.setCode = item.set_code;

                div.addEventListener('click', function () {
                    hiddenSetCode.value = item.set_code;
                    input.value = '';
                    closePreview();
                    showSetCodeTag(item.set_code);
                    input.closest('form').submit();
                });

                previewBox.appendChild(div);
            });
        }

        // Botón "Ver todos los resultados"
        var viewAll = document.createElement('a');
        viewAll.className = 'preview-view-all';
        viewAll.href = '/search-cards/?q=' + encodeURIComponent(term);
        viewAll.textContent = 'View all results for "' + term + '"';
        viewAll.addEventListener('click', function () {
            closePreview();
        });
        previewBox.appendChild(viewAll);

        previewBox.classList.add('active');
        overlay.classList.add('active');
    }

    function highlightMatch(text, term) {
        var escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var regex = new RegExp('(' + escaped + ')', 'gi');
        return escapeHtml(text).replace(regex, '<strong>$1</strong>');
    }

    function showSetCodeTag(code) {
        isSetCodeSelected = true;
        var existingTag = document.querySelector('.setcode-tag');
        if (existingTag) existingTag.remove();

        var tag = document.createElement('span');
        tag.className = 'setcode-tag';
        tag.innerHTML = '<span class="setcode-tag-text">Set: ' + escapeHtml(code) + '</span>' +
                        '<span class="setcode-tag-remove">&times;</span>';

        tag.querySelector('.setcode-tag-remove').addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            removeSetCodeTag();
        });

        input.parentNode.insertBefore(tag, input);
        input.placeholder = 'Search cards in ' + code + '...';
    }

    function removeSetCodeTag() {
        isSetCodeSelected = false;
        hiddenSetCode.value = '';
        var tag = document.querySelector('.setcode-tag');
        if (tag) tag.remove();
        input.placeholder = 'Search cards by name or Set Code (e.g. LOB-005)';
        input.focus();
    }

    function updateActive(items) {
        items.forEach(function (item, i) {
            item.classList.toggle('active', i === activeIndex);
        });
        if (items[activeIndex]) {
            items[activeIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    function closePreview() {
        previewBox.classList.remove('active');
        overlay.classList.remove('active');
        previewBox.innerHTML = '';
        activeIndex = -1;
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
