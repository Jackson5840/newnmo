$(function () {

    $.getJSON('/json/acknowledgement.json', function(ackData) {               
        $.each(ackData.data, function(index, ack) {
            labName = '<li>' + ack.lab_name + '</li>'
            labDepartment = '<a>' + ack.lab_department + '</a>'
            breakLine = '<br>'
            labLocation = '<a>' + ack.lab_location + '</a>'
            $("#acknowledgementList").append(labName, labDepartment, breakLine, labLocation)
        });

    });

});