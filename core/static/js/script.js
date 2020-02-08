$(function() {
  // show up arrow
  $(window).scroll(function() {
    if ($(window).scrollTop() > 800) {
      $('#up-arrow').show();
    } else {
      $('#up-arrow').hide();
    }
  });

  // move to top of page
  $('#up-arrow').click(function() {
    $(window).scrollTop(0);
  });
});
