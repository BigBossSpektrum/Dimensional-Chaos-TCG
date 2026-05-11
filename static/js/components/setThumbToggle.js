const VISIBLE_COUNT = 3;
let _modalSourceContainer = null;

function toggleSets(btn) {
    openSetModal(btn.previousElementSibling);
}

function openSetModal(container) {
    _modalSourceContainer = container;
    var modal = document.getElementById('setModal') || _createSetModal();
    var grid = modal.querySelector('.setModal-grid');
    grid.innerHTML = '';

    container.querySelectorAll('.setThumb').forEach(function(thumb, i) {
        var item = document.createElement('div');
        item.className = 'setThumb' + (thumb.classList.contains('setThumb--active') ? ' setThumb--active' : '');
        item.innerHTML = thumb.innerHTML;
        item.addEventListener('click', (function(idx) {
            return function() { _selectFromModal(idx); };
        })(i));
        grid.appendChild(item);
    });

    modal.classList.add('setModal--open');
}

function _selectFromModal(index) {
    if (!_modalSourceContainer) return;
    var original = _modalSourceContainer.querySelectorAll('.setThumb')[index];
    if (original) switchSet(original);
    closeSetModal();
}

function closeSetModal() {
    var modal = document.getElementById('setModal');
    if (modal) modal.classList.remove('setModal--open');
    _modalSourceContainer = null;
}

function _createSetModal() {
    var modal = document.createElement('div');
    modal.id = 'setModal';
    modal.className = 'setModal';
    modal.innerHTML =
        '<div class="setModal-backdrop"></div>' +
        '<div class="setModal-dialog">' +
            '<div class="setModal-header">' +
                '<span class="setModal-title">Sets / Rarities</span>' +
                '<button class="setModal-close">&times;</button>' +
            '</div>' +
            '<div class="setModal-grid"></div>' +
        '</div>';

    modal.querySelector('.setModal-backdrop').addEventListener('click', closeSetModal);
    modal.querySelector('.setModal-close').addEventListener('click', closeSetModal);
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeSetModal(); });
    document.body.appendChild(modal);
    return modal;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.setThumbnails').forEach(function(container) {
        var thumbs = container.querySelectorAll('.setThumb');
        if (thumbs.length > VISIBLE_COUNT) {
            thumbs.forEach(function(s, i) { if (i >= VISIBLE_COUNT) s.classList.add('setThumb--hidden'); });
            var btn = container.nextElementSibling;
            if (btn && btn.classList.contains('setThumb-toggle')) {
                btn.textContent = '+ ' + (thumbs.length - VISIBLE_COUNT) + ' más';
            }
        }
    });
});
