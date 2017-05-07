
$('.tab a').click(function(event) {
    event.preventDefault();
    $(this).tab('show');
});

$('input[type=checkbox]').click(function(event) {
    var input = $('#' + $(this).data('target'));
    var checked = $(this).is(':checked');
    input.prop('disabled', !checked);
});
