$(document).ready(function(){

  // Dropdown example for topbar nav
  // ===============================

  $("body").bind("click", function (e) {
    $('.dropdown-toggle, .menu').parent("li").removeClass("open");
  });
  $(".dropdown-toggle, .menu").click(function (e) {
    var $li = $(this).parent("li").toggleClass('open');
    return false;
  });
  
  renderSnippet('http://javasoze.github.com/sin/home.html',$('#homeLink'));

});
