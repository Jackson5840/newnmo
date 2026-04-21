$(function () {

    $.getJSON('/json/whats-new.json', function(archiveData) {               
        $.each(archiveData.data, function(index, ach) {
            archiveInfo = '<div class="col-md-3">' +
                             '<div class="card mb-4 shadow-sm">' +
                                '<img class="img-fluid" src="' + ach.archive_img + '">' +
                                '<div class="card-body">' +
                                    '<div class="d-flex justify-content-between align-items-center">' +
                                        '<div class="col text-center"><a>'+ ach.archive_size +' neurons</a><br><a>' + ach.archive_release  + '</a><br>' +
                                        '<a class="btn btn-sm btn-outline-secondary" href="' + ach.archive_link +'">' + ach.archive_name  + '</a></div>' +
                                '</div>' +
                            '</div>' +
                        '</div>' +
                    '</div>';

            $("#archiveInfo").append(archiveInfo)
        });

    });

});


