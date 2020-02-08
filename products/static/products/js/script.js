$(function() {
  // submit form when sort changes
  $('#item-sort').change(function() {
    $('#filter-form').submit();
  });

  // don't submit keywords if empty
  $('#filter-form').submit(function() {
    if (!$('#keyword-filter').val()) {
      $('#keyword-filter').attr('name', '');
    }
  });

  // update filter form with url params
  $.each(query, function(key, lst) {
    $.each(lst, function(idx, val) {
      if ($('[name=' + key + ']').is('input[type="checkbox"]')) {
        $('[value=' + val + ']').prop('checked', true);
      } else if ($('[name=' + key + ']').is('select')) {
        $('[value=' + val + ']').prop('selected', true);
      } else if ($('[name=' + key + ']').is('input[type="search"]')) {
        $('input[name=' + key + ']').val(val);
      }
    });
  });

  // load more items with ajax
  $('#load-more button').click(function() {
    var page = parseInt($('#page').val());
    var button = $(this);
    query['page'] = page;

    $(button).prop('disabled', true);
    $(button).text('Loading...');

    $.ajax({
      method: 'GET',
      url: path,
      data: query,
      dataType: 'json',
      traditional: true,
      success: function(data) {
        query['page'] = page + 1;

        if (page * 20 < parseInt(results)) {
          $(button).text('Load More Results');
          $('#page').val(page + 1);
          $(button).prop('disabled', false);
        } else {
          $(button).parent().remove();
        }

        $('#item-container').append(data.items_html);
      }
    });

    // add carousel to new items
    $(document).ajaxStop(function() {
      $('.item-gallery:not(.slick-slider)').slick({
        prevArrow: '<div class="slick-prev"><img src="/static/img/arrow.png" /></div>',
        nextArrow: '<div class="slick-next"><img src="/static/img/arrow.png" /></div>',
      });
    });
  });

  // show filters on click
  $('#show-filter-btn').click(function() {
    if ($('#item-filters').is(':visible')) {
      $('#item-filters').css('display', 'none');
      $(this).html('Show Filters');
    } else {
      $('#item-filters').css('display', 'inline-block');
      $(this).html('Hide Filters');
    }
  });

  // show/hide text on click
  $('#item-container').on('click', '.text-btn', function() {
    var text = $(this).parent().parent().find('.item-text');
    if (text.is(':visible')) {
      text.hide();
      $(this).html('Show Text');
    } else {
      text.show();
      $(this).html('Hide Text');
    }
  });
  $('#item-container').on('click', '.item-text', function() {
    $(this).hide();
    $(this).parent().find('.text-btn').html('Show Text');
  });

  // item image gallery
  $('.item-gallery').slick({
    prevArrow: '<div class="slick-prev"><img src="/static/img/arrow.png" /></div>',
    nextArrow: '<div class="slick-next"><img src="/static/img/arrow.png" /></div>',
  });
});
