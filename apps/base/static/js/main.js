$(function() {
  $('.comments  .ajax-vote').on("click", function (e) {
    e.preventDefault();
    var value = 1;
    if ($(this).hasClass('minus')) {
      value = -1;
    }
    if ($(this).hasClass('plus')) {
      value = 1;
    }
    var container = $(this).siblings('span').get(0);
    $.post($(this).attr('data-href'),
        {},
        function (data, textStatus, xhr) {
          if ([201, 200].indexOf(xhr.status) + 1) {
            var new_value = parseInt($(container).text()) + value;
            var msg = 'Ваше мнение учтёно, спасибо!';
            if (xhr.status == 200) {
              new_value += value;
              msg = 'Ваше мнение изменено, спасибо!';
            }
            if (new_value > 0) {
              new_value = '+' + new_value;
            }
            $(container).text(new_value);
            notif({
              msg: msg,
              type: 'success'
            });
          } else if (xhr.status == 304) {
            notif({
              msg: 'Голос уже учтён, спасибо!',
              type: 'notice'
            });
          }
        }
    );
  });
});
