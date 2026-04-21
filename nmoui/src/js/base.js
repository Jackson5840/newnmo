//const apiurlbase = 'https://neuromorpho.org/newapi'
//const apiurlbase = 'http://cng-nmo-main.orc.gmu.edu:8002'
const apiurlbase = '/api';

async function getneurons(params) {
    var qstring = new URLSearchParams(params);
    if (params.has("keyword")) {
        apiurl = '/search/' + params.get('keyword')
    }
    else {
        apiurl = `/neuron/?${qstring}`
    }
    const result = await fetch(apiurlbase + apiurl, {
        method: "get"
      })
      .then((response) => {
        return response.json()
    });
      //.then(res => {
      //  return res.data;
      //  })
    return result
}

async function getfieldvals(fields,parent='',idlistkey='') {
    params = new URLSearchParams()
    fields.forEach(element => {
        params.append('fields',element)
    });
    if (parent != '') {
        params.append('parent',parent)
    }
    if (idlistkey != '') {
        params.append('idlistkey',idlistkey)
    }
    const result = await fetch(apiurlbase + `/metavals/?${params}`, {
        method: "get"
      })
      .then((response) => {
        return response.json()
    });
      //.then(res => {
      //  return res.data;
      //  })
    return result
}

async function getmeasurements(name) {
    const result = await fetch(apiurlbase + `/measurements/?name=${name}`, {
        method: "get",
        mode: 'cors'
      })
      .then((response) => {
        return response.json()
    });
      //.then(res => {
      //  return res.data;
      //  })
    return result
}

async function getpvec(name) {
    const result = await fetch(apiurlbase + `/pvec/${name}`, {
        method: "get",
        mode: 'cors'
      })
      .then((response) => {
        return response.json()
    });
      //.then(res => {
      //  return res.data;
      //  })
    return result
}

function maketree(specval,fieldname,treeid,imageid,idlistkey='') {
    if (idlistkey != '') {
        idliststr = '?idlistkey=' + idlistkey;
    }
    else {
        idliststr = ''; 
    }
    $.getJSON(apiurlbase + "/browse/" + fieldname+ "/" + specval + idliststr, function(datalist) {     
        if (datalist.data[0].children.length > 0) {  
            if (document.getElementById(treeid).classList.contains('jstree')) {$('#'+treeid).jstree('destroy'); }      
            $('#' +treeid).jstree({ 
                'core' : datalist,
                'checkbox': {
                'whole_node': false
                },
                "conditionalselect" : function (node, event) {
                if (event.target.classList.contains('jstree-checkbox')) {
                    return true;
                }
                else if (node.children.length > 0) {
                    return false;
                }
                else {
                    window.open(event.currentTarget.href,'_blank');
                    return false;
                }
                
                },
                "plugins" : [ "checkbox","conditionalselect" ]
            }).on('hover_node.jstree', function(e, data) {
                var $node = $("#" + data.node.id);
                var url = $node.find('a').attr('imgurl');
                if (url) {
        
                //            $("#" + data.node.id).prop('title', url);
                $('#'+imageid).find('img').attr('src', url);
                $('#'+imageid)
                    .css('position', 'absolute')
                    .css('top', $node.position().top) // Add about 20 to ensure the div is not hovered when we re-position it.
                    .css('left', $node.position().left + $node.width() + 20)
                    //.css('top', mouse_y)
                    //.css('left', mouse_x + 100)
                    .show();
            }
            })
            .on('dehover_node.jstree', function() {
                $('#' + imageid).hide(); // Need to hide tooltip after we change hover targets.
            });
        }
    });  
  }
  

function parseneuronlist(neuronlist,target) {
    // parses a list of neurons to target

    var domains = {
        'PR': 'Process',
        'NEU': 'Neurites',
        'AX': 'Axon'
    }

    var neuronhtml = '<div class="row">'
    var i= -1
    neuronlist.forEach(element => {
        i++ ;

        // make value specific computations
        var nreg = element.region_array.length;
        var region2 = (nreg > 1 ? element.region_array[1] : 'Not reported');
        var region3 = (nreg > 2 ? element.region_array[2] : 'Not reported');
        var ncell = element.celltype_array.length;
        var cell2 = (ncell > 1 ? element.celltype_array[1] : 'Not reported');
        var cell3 = (ncell > 2 ? element.celltype_array[2] : 'Not reported');

        var physint = '';
        var structdom = '';

        var dendrites = true;
        var nojump = true;
        var j = 0;
        element.structural_domain.forEach(selem => {
            if (j>0 && nojump) {
                structdom += ', ';
                physint += ', ';
            }
            if (['AP','BS'].includes(selem.domain)) {
                if (dendrites) {
                    dendrites = false;
                    structdom += 'Dendrites';
                    physint += 'Dendrites ' + selem.completeness;                        
                    nojump= true;
                }
                else {
                    nojump = false;
                }
            }
            else {
                structdom += domains[selem.domain];
                physint += domains[selem.domain] + ' ' + selem.completeness;
                nojump= true;
            }
            j++;
        });



        
        var namearr = element.name.match(/.{1,32}/g);
        var neuronname = namearr.join(' ');

        if ((i % 3) == 0) {
            //neuronhtml += '</div><div class="row">'
        }
        neuronhtml += `
        <div class="col-md-4">
            <div class="card mb-4 shadow-sm">
                <img class="img-fluid" loading="lazy" src="${element.png_url}" />
                <div class="card-body">
                    <table class="table-striped table-sm">
                        <tr>
                            <td colspan=2 style="text-align: center"><b>${neuronname}</b></td>
                        </tr>
                        <tr>
                            <td>Archive Name</td>
                            <td>${element.archive_name}</td>
                        </tr>
                        <tr>
                            <td>Species Name</td>
                            <td>${element.species_name}</td>
                        </tr>
                        <tr>
                            <td>Structural Domains</td>
                            <td>${structdom}</td>
                        </tr>
                        <tr>
                            <td>Physical Integrity</td>
                            <td>${physint}</td>
                        </tr>
                        <tr>
                            <td>Morphological Attributes</td>
                            <td>${element.structural_domain[0].morph_attributes}</td>
                        </tr>
                        <tr>
                            <td>Region1</td>
                            <td>${element.region_array[0]}</td>
                        </tr>
                        <tr>
                            <td>Region2</td>
                            <td>${region2}</td>
                        </tr>
                        <tr>
                            <td>Region3</td>
                            <td>${region3}</td>
                        </tr>
                        <tr>
                            <td>Main Cell Type</td>
                            <td>${element.celltype_array[0]}</td>
                        </tr>
                        <tr>
                            <td>Class2</td>
                            <td>${cell2}</td>
                        </tr>
                        <tr>
                            <td>Class3</td>
                            <td>${cell3}</td>
                        </tr>
                    </table>
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="col text-center"><a class="btn btn-success btn-sm" href="neuroninfo.html?name=${element.name}">View</a></div>
                        <div class="form-check">
                            <input class="form-check-input dlcheck" type="checkbox" value="" id="${element.name}">
                            <label class="form-check-label" for="flexCheckDefault">
                                Download
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `
        
    });
    neuronhtml += '</div>'
    
    console.log(neuronhtml);
    document.getElementById(target).innerHTML = neuronhtml;
}



function download(filename, text) {
    var element = document.createElement('a');
    
  
    element.style.display = 'none';
    document.body.appendChild(element);
  
    element.click();
  
    document.body.removeChild(element);
  }
  
  // Start file download.
  download("hello.txt","This is the content of my file :)");
  