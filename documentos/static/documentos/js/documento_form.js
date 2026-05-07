document.addEventListener('DOMContentLoaded', function () {
    var entidadeSelect = document.getElementById('id_entidade');
    var objetoSelect   = document.getElementById('id_objeto');
    var tipoSelect     = document.getElementById('id_tipo');

    if (!entidadeSelect || !objetoSelect || !tipoSelect) return;

    function resetSelect(sel, placeholder) {
        sel.innerHTML = '<option value="">' + placeholder + '</option>';
    }

    function populateSelect(sel, items, valueKey, labelKey, preserveValue) {
        var current = preserveValue !== undefined ? preserveValue : sel.value;
        sel.innerHTML = '<option value="">---------</option>';
        items.forEach(function (item) {
            var opt = document.createElement('option');
            opt.value   = item[valueKey];
            opt.textContent = item[labelKey];
            sel.appendChild(opt);
        });
        if (current) sel.value = current;
    }

    function fetchAndPopulate(ctId, preserveObjeto, preserveTipo) {
        if (!ctId) {
            resetSelect(objetoSelect, '---------');
            return;
        }
        fetch('/documentos/ajax/objetos/?ct=' + ctId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                populateSelect(objetoSelect, data.objetos, 'id',    'texto',  preserveObjeto);
                populateSelect(tipoSelect,   data.tipos,   'valor', 'label',  preserveTipo);
                // notifica Alpine.js sobre a mudança no campo tipo
                tipoSelect.dispatchEvent(new Event('input',  { bubbles: true }));
                tipoSelect.dispatchEvent(new Event('change', { bubbles: true }));
            });
    }

    // ao carregar a página em modo edição, repovoar selects preservando valores atuais
    if (entidadeSelect.value) {
        fetchAndPopulate(entidadeSelect.value, objetoSelect.value, tipoSelect.value);
    }

    entidadeSelect.addEventListener('change', function () {
        fetchAndPopulate(this.value, '', '');
    });
});
