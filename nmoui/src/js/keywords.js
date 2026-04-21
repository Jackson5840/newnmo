function metasearch(countonly=false) {
    theform = document.getElementById('searchform');
    var formdata = new FormData(theform);
    params = new URLSearchParams();
    for (var pair of formdata.entries()) {
        params.append(pair[0],pair[1]);
      }
    if (countonly) {
        getneurons(params).then(response => {
            document.getElementById('nneurons').innerHTML = response.total
        })
    }
    else {
        window.location= './neurons.html?' + params
    }

    //getneurons(params).then(response => {
    //    console.log(response)
    //})

}