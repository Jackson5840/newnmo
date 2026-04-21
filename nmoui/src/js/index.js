$(function () {

    $.getJSON(apiurlbase + '/neuron/?random=9', function(imgData) {             
        var activestring = 'active';
        $.each(imgData.data.slice(0,3), function(index, img) {
            $("#carousel1").append(`<div class="carousel-item ${activestring}"><img class="d-block img-fluid" style="width:100%;max-width=150;aspect-ratio: 4/3;" src="${img.png_url}"></div>`);
            activestring = '';
        });
        var activestring = 'active';
        $.each(imgData.data.slice(3,6), function(index, img) {
            $("#carousel2").append(`<div class="carousel-item ${activestring}"><img class="d-block img-fluid" style="width:100%;max-width=150;aspect-ratio: 4/3;" src="${img.png_url}"></div>`);
            activestring = '';
        });
        var activestring = 'active';
        $.each(imgData.data.slice(6,9), function(index, img) {
            $("#carousel3").append(`<div class="carousel-item ${activestring}"><img class="d-block img-fluid" style="width:100%;max-width=150;aspect-ratio: 4/3;" src="${img.png_url}"></div>`);
            activestring = '';
        });
    });

/*     $.getJSON(apiurlbase + '/neuron/?random=3', function(imgData) {               
        $.each(imgData.data, function(index, img) {
            $("#imgCollection").append(`<img class="img-fluid" style="width:200px;" src="${img.png_url}"></img>`)
        });

    });

    $.getJSON(apiurlbase + '/neuron/?random=3', function(imgData) {               
        $.each(imgData.data, function(index, img) {
            $("#imgCollection").append(`<img class="img-fluid" style="width:200px;" src="${img.png_url}"></img>`)
        });

    }); */

});
