function formatCpfCnpj(raw) {
    var d = raw.replace(/\D/g, '').slice(0, 14);
    if (d.length <= 11) {
        if (d.length > 9) return d.slice(0,3)+'.'+d.slice(3,6)+'.'+d.slice(6,9)+'-'+d.slice(9);
        if (d.length > 6) return d.slice(0,3)+'.'+d.slice(3,6)+'.'+d.slice(6);
        if (d.length > 3) return d.slice(0,3)+'.'+d.slice(3);
        return d;
    } else {
        if (d.length > 12) return d.slice(0,2)+'.'+d.slice(2,5)+'.'+d.slice(5,8)+'/'+d.slice(8,12)+'-'+d.slice(12);
        if (d.length > 8)  return d.slice(0,2)+'.'+d.slice(2,5)+'.'+d.slice(5,8)+'/'+d.slice(8);
        if (d.length > 5)  return d.slice(0,2)+'.'+d.slice(2,5)+'.'+d.slice(5);
        if (d.length > 2)  return d.slice(0,2)+'.'+d.slice(2);
        return d;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-cpf-cnpj-mask]').forEach(function (input) {
        input.addEventListener('input', function (e) {
            var cursor = e.target.selectionStart;
            var oldLen = e.target.value.length;
            e.target.value = formatCpfCnpj(e.target.value);
            // ajusta cursor para não pular após separadores
            var diff = e.target.value.length - oldLen;
            e.target.setSelectionRange(cursor + diff, cursor + diff);
        });
    });
});
