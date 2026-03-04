document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('sendData');
    const hiddenSetCode = document.getElementById('setCodeHidden');
    const suggestionsBox = document.getElementById('setCodeSuggestions');
    if (!input || !suggestionsBox || !hiddenSetCode) return;

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

        // Limpiar set_code oculto si el usuario edita el texto
        if (isSetCodeSelected) {
            // No buscar sugerencias mientras hay un tag activo
            return;
        }

        if (term.length < 3) {
            closeSuggestions();
            return;
        }

        debounceTimer = setTimeout(function () {
            fetch('/api/suggest-set-codes/?term=' + encodeURIComponent(term))
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    renderSuggestions(data);
                })
                .catch(function () {
                    closeSuggestions();
                });
        }, 300);
    });

    input.addEventListener('keydown', function (e) {
        const items = suggestionsBox.querySelectorAll('.setcode-suggestion-item');

        if (items.length) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, items.length - 1);
                updateActive(items);
                return;
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                updateActive(items);
                return;
            } else if (e.key === 'Enter' && activeIndex >= 0) {
                e.preventDefault();
                selectItem(items[activeIndex]);
                return;
            } else if (e.key === 'Escape') {
                closeSuggestions();
                return;
            }
        }
    });

    // Cerrar sugerencias al hacer clic fuera
    document.addEventListener('click', function (e) {
        if (!input.contains(e.target) && !suggestionsBox.contains(e.target)) {
            closeSuggestions();
        }
    });

    function renderSuggestions(data) {
        suggestionsBox.innerHTML = '';
        activeIndex = -1;

        if (!data.length) {
            closeSuggestions();
            return;
        }

        data.forEach(function (item) {
            const div = document.createElement('div');
            div.className = 'setcode-suggestion-item';
            div.innerHTML =
                '<span class="set-code-label">' + escapeHtml(item.set_code) + '</span>' +
                '<span class="set-name-label">' + escapeHtml(item.set_name) + '</span>';

            div.addEventListener('click', function () {
                selectItem(div, item.set_code);
            });
            div.dataset.setCode = item.set_code;
            suggestionsBox.appendChild(div);
        });

        suggestionsBox.classList.add('active');
    }

    function selectItem(el, code) {
        const selectedCode = code || el.dataset.setCode;
        hiddenSetCode.value = selectedCode;
        input.value = '';
        closeSuggestions();
        showSetCodeTag(selectedCode);
        // Enviar el formulario automáticamente
        input.closest('form').submit();
    }

    function showSetCodeTag(code) {
        isSetCodeSelected = true;
        // Remover tag existente si hay uno
        const existingTag = document.querySelector('.setcode-tag');
        if (existingTag) existingTag.remove();

        const tag = document.createElement('span');
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
        const tag = document.querySelector('.setcode-tag');
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

    function closeSuggestions() {
        suggestionsBox.classList.remove('active');
        suggestionsBox.innerHTML = '';
        activeIndex = -1;
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
