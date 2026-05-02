document.addEventListener('DOMContentLoaded', function () {
    var estadoInput = document.getElementById('id_estado');
    var cidadeInput = document.querySelector('[data-cidade-field]');

    if (!estadoInput || !cidadeInput) return;

    var datalistId = cidadeInput.getAttribute('list');
    var datalist = document.getElementById(datalistId);
    var data = window.__cidadesPorEstado || {};

    function updateCidades() {
        var estado = estadoInput.value.trim().toUpperCase();
        var cidades = data[estado] || [];
        datalist.innerHTML = cidades.map(function (c) {
            return '<option value="' + c + '">';
        }).join('');
    }

    estadoInput.addEventListener('input', updateCidades);
    estadoInput.addEventListener('change', updateCidades);
    updateCidades();
});
