$(document).ready(function($) {
    'use strict';

    // Gestion des onglets
    $('.tab a').click(function (event) {
        event.preventDefault();
        $(this).tab('show');
    });

    // (Dés)activation des contrôles ciblés par des cases à cocher
    $('input[type=checkbox]').click(function (event) {
        let input = $('#' + $(this).data('target'));
        let checked = $(this).is(':checked');
        input.prop('disabled', !checked);
    });

    // Génération des listes avec recherche
    $('.select2').select2();
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (event) {
        localStorage.activePanel = event.target.id;
        $('.select2').select2();
    });

    // Affichage du premier onglet par défaut
    if ($('.tab-pane.active').length === 0) {
        let activePanel = $('#' + localStorage.activePanel);
        if (activePanel.length) {
            activePanel.click();
        } else {
            $('.tab a:first').click();
        }
    }

    // Jets de dés
    let diceRoller = new DiceRoller();

    $('#diceroll').on('shown.bs.modal', function () {
        $('#diceroll-input').trigger('focus').select();
    });

    $('#diceroll-form').on('submit', function () {
        let value = $('#diceroll-input').val();
        let roll = diceRoller.roll(value);
        $('#diceroll-output').val(roll.getNotation());
        return false;
    });

    $.key('ctrl+space', function () {
        $('#diceroll').modal();
    });

    // Popups
    $('[data-toggle="tooltip"]').tooltip();

    // Simulation
    $('[data-simulation]').on('click', function () {
        let form = $($(this).data('simulation'));
        let data = {};
        $.each(form.serializeArray(), function (i, e) {
            let current = data[e.name];
            if (Array.isArray(current)) {
                data[e.name].push(e.value);
            } else if (current !== undefined) {
                data[e.name] = [current];
                data[e.name].push(e.value);
            } else data[e.name] = e.value;
        });
        $.post('/simulation/', data, function (result) {
            if (result !== '') {
                if (typeof result == 'string') {
                    alert(result);
                } else if (Array.isArray(result)) {
                    let messages = [];
                    $.each(result, function (i, e) {
                        messages.push(e.description);
                    });
                    alert(messages.join('\n\n'))
                } else if (result.fail) {
                    alert(`${result.description}\n\n${result.fail.description}`)
                } else alert(`${result.description}`);
            }
        });
    });

    // Désactiver le re-POST
    window.history.replaceState(null, document.title, location.href);
});