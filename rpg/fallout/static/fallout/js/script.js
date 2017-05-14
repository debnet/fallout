
// Gestion des onglets
$('.tab a').click(function(event) {
    event.preventDefault();
    $(this).tab('show');
});

// (Dés)activation des contrôles ciblés par des cases à cocher
$('input[type=checkbox]').click(function(event) {
    var input = $('#' + $(this).data('target'));
    var checked = $(this).is(':checked');
    input.prop('disabled', !checked);
});

// Affichage du premier onglet par défaut
if ($('.tab-pane.active').length === 0) {
    $('.tab a:first').click();
}
