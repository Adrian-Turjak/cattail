$(document).ready(function(){
    // Initializes tooltips
    $('[title]').tooltip({container: 'body'});

    //Apply img-thumbnail class to rich-content images
    $('.rich-content img').addClass("img-thumbnail");
});