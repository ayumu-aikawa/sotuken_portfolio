$(function() {
   const hum = $('#hamburger, .close')
   const nav = $('.sp-nav')
   hum.on('click', function(){
      nav.toggleClass('toggle');
   });
});

//  注意  終了ボタンでセッションを切る仕様 
$(function(){
    $('#stop').click(function() {
        localStorage.removeItem('no_camera_check');
    });
});

$(function(){
    $('.camera_check').click(function(){
        if (localStorage.getItem('no_camera_check') == 'no_camera_check'){
            window.location.href="/sotuken/camera";
        }else{
            window.location.href="/sotuken/camera/check";
        }
    });
});

$(function() {
    $('body').fadeIn(1000); //1秒かけてフェードイン！
});