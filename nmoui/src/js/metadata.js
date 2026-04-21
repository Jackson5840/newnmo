//import {getfieldvals, getneurons} from './base.js'

/*$(function () {
    $(document).on('click', '#resetMetadata', function() { 
        console.log("Check!")
        window.location.reload();
    });

})*/
var fields = ['species_name','originalformat_name','age','archive_name','objective','uploaddate','depositiondate','protocol','staining_name','slicing_direction','reconstruction','magnification','publication_pmid','expcond_name','slicingthickness','max_age','min_age','min_weight','max_weight','gender','shrinkage'];
var sendfields = ['species_name','originalformat_name','age','archive_name','objective','uploaddate','depositiondate','protocol','staining_name','slicing_direction','reconstruction','magnification','publication_pmid','expcond_name','slicingthickness','max_age','min_age','min_weight','max_weight','gender','shrinkage','morph_attributes','structural_domain','domain','completeness'];

function resetinput() {
    var elements = document.getElementsByClassName('.selectpicker');
    for (const item of elements) {
        item.val('default');
        item.selectpicker('refresh');
        item.data('selectpicker').$searchbox.val('').trigger('propertychange');
        
    }
}

function updatemenu(field) {
    tofetch = true;
    if (field == 'morph_attributes') {
        tofetch = false;
        data = {
            1: "Diameter, 2D, Angles",
            2: "Diameter, 3D, No Angles",
            3: "Diameter, 3D, Angles",
            4: "Diameter, 2D, No Angles",
            5: "No Diameter, 2D, Angles",
            7: "No Diameter, 3D, Angles"
        }
    }
    else if (field == "struct_domain") {
        tofetch = false;
        data = {
            1: "Dendrites, No Soma, Axon", 
            2: "Dendrites, No Soma, No Axon", 
            3: "Dendrites, Soma, Axon", 
            4: "Dendrites, Soma, No Axon", 
            5: "Neurites, No Soma", 
            6: "Neurites, Soma", 
            7: "No Dendrites, No Soma, Axon", 
            8: "No Dendrites, Soma, Axon", 
            9: "Processes, No Soma", 
            10: "Processes, Soma"
        }
    }

    if (tofetch)  {
        getfieldvals([field]).then(data => {
            data.forEach(elem => {
                var output = [];

                $.each(elem.vals, function(key,value)
                {
                    output.push('<option value="'+ value +'">'+ value +'</option>');
                });

                $('#' + elem.field).html(output.join(''));
                $('#' + elem.field).selectpicker('refresh');
            });
        });
    }
    else {
        var output = [];
        for (const key in data) {
            output.push('<option value="'+ key +'">'+ data[key] +'</option>');
        }
        $('#' + field).html(output.join(''));
        $('#' + field).selectpicker('refresh');
    }
}

function updatelevel(field,parent='') {
    getfieldvals([field],parent).then(data => {
        data.forEach(elem => {
            var output = [];

            $.each(elem.vals, function(key,value)
            {
                output.push('<option value="'+ value.path +'">'+ value.name +'</option>');
            });

            $('#' + elem.field).html(output.join(''));
            $('#' + elem.field).selectpicker('refresh');
        });
    });
}


function addfilter(field,label) {
    // adds option to selection part and removes from filter part 
    filtbutton = document.getElementById(field+'_button');
    filtbutton.setAttribute('class','btn btn-success m-1');
    filtselect = document.createElement("select");
    filtselect.setAttribute('class','selectpicker'); 
    
    filtselect.setAttribute('name',field);
    filtselect.setAttribute('data-live-search',field);
    filtselect.setAttribute('id',field);
    filtselect.setAttribute('title',label);
    filtselect.setAttribute('data-width',"100%");
    if (['max_age','min_age','min_weight','max_weight'].includes(field)) {
        opselect  = document.createElement("select");
        opselect.setAttribute('id',field+'_op');
        opselect.setAttribute('name',field+'_op');
        opselect.setAttribute('class','selectpicker');
        opselect.setAttribute('title','Select operand');
        opselect.setAttribute('data-width',"100%");
        var output = [];
        data = [['>','&gt;'],['<','&lt;'],['=','='],['<=','&le;'],['>=','&ge;']]
        data.forEach(elem => {
            output.push('<option value="'+ elem[0] +'">'+ elem[1] +'</option>');
        });

        opselect.innerHTML = output.join('');
        //opselect.selectpicker('refresh');
        //TODO populate first listbox
        var arow = document.createElement('div');
        arow.setAttribute('class','row');        
        var acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(filtselect);
        arow.appendChild(acol);
        acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(opselect);
        arow.appendChild(acol);
        updatemenu(field);
        document.getElementById('selectlist').appendChild(arow);
        $('#' + field +'_op').selectpicker('refresh');
        $('#' + field).selectpicker('refresh'); 
        //complexrow.appendChild(filtselect)
        //complexrow.appendChild(opselect)
        //document.getElementById('selectlist').appendChild(complexrow);

    }
    else if (['region','celltype'].includes(field)) {
        filtselect.setAttribute('id',field+'1');
        filtselect.setAttribute('name',field+'1');
        //filtselect.onchange =updatelevel('region2',this.value)
        
        updatelevel(field+'1');
        lev2select  = document.createElement("select");
        lev2select.setAttribute('id',field+'2');
        lev2select.setAttribute('name',field+'2');
        lev2select.setAttribute('class','selectpicker');
        //lev2select.setAttribute('diabled','true');
        lev2select.setAttribute('title','Select lev. 2');
        lev2select.setAttribute('data-width',"100%");
        

        lev3select  = document.createElement("select");
        lev3select.setAttribute('id',field+'3');
        lev3select.setAttribute('name',field+'3');
        lev3select.setAttribute('class','selectpicker');
        //lev2select.setAttribute('diabled','true');
        lev3select.setAttribute('title','Select lev. 3');
        lev3select.setAttribute('data-width',"100%");

        lev2select.addEventListener("change",function() {
            updatelevel(field + '3',this.value);
        })

        filtselect.addEventListener("change",function() {
            updatelevel(field + '2',this.value);
            lev3select.value = 0;
            $('#' + field+'3').selectpicker('refresh'); 
            
        })

        var arow = document.createElement('div');
        arow.setAttribute('class','row');        
        var acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(filtselect);
        arow.appendChild(acol);
        acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(lev2select);
        arow.appendChild(acol);

        acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(lev3select);
        arow.appendChild(acol);

        document.getElementById('selectlist').appendChild(arow);
        $('#' + field +'_2').selectpicker('refresh');
        $('#' + field +'_3').selectpicker('refresh');
        $('#' + field).selectpicker('refresh'); 
    } 
    else if (field == "physint") {
        filtselect.setAttribute('id',field);
        filtselect.setAttribute('name',field);
        //filtselect.onchange =updatelevel('region2',this.value)
        data = {
            1: "Search by Dendrites", 
            2: "Search by Axon", 
            3: "Search by Dendrites &amp; Axon", 
            4: "Search by Neurites", 
            5: "Search by Processes"
        }
        var output = [];
        for (const key in data) {
            output.push('<option value="'+ key +'">'+ data[key] +'</option>');
        }
        $('#physint').html(output.join(''));
        $('#physint').selectpicker('refresh');
       
        
        


        data2 = {
            0: "Incomplete",
            1: "Moderate",
            2: "Complete"
        };

        data3 = {
            0: "Dendrites & Axon Complete",
            1: "Dendrites & Axon Moderate",
            2: "Dendrites & Axon Incomplete",
            3: "Dendrites Complete, Axon Moderate",
            4: "Dendrites Complete, Axon Incomplete",
            5: "Dendrites Moderate, Axon Complete",
            6: "Dendrites Moderate, Axon Incomplete",
            7: "Dendrites Incomplete, Axon Complete",
            8: "Dendrites Incomlete, Axon Moderate"
        }

        filtselect.addEventListener("change",function() {
            if (this.value==3) {
                data = data3;
            }
            else {
                data = data2;
            }
            var output = [];
            for (const key in data) {
                output.push('<option value="'+ key +'">'+ data[key] +'</option>');
            }
            $('#physint2').html(output.join(''));
            $('#physint2').selectpicker('refresh');
            
        })

        lev2select  = document.createElement("select");
        lev2select.setAttribute('id',field+'2');
        lev2select.setAttribute('name',field+'2');
        lev2select.setAttribute('class','selectpicker');
        //lev2select.setAttribute('diabled','true');
        lev2select.setAttribute('title','Select Completeness');
        lev2select.setAttribute('data-width',"100%");
        var arow = document.createElement('div');
        arow.setAttribute('class','row');        
        var acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(filtselect);
        arow.appendChild(acol);
        acol = document.createElement('div');
        acol.setAttribute('class','col');
        acol.appendChild(lev2select);
        arow.appendChild(acol);
        document.getElementById('selectlist').appendChild(arow);
        $('#physint').html(output.join(''));
        $('#physint').selectpicker('refresh');

    }
    else {
        filtselect.setAttribute('multiple',''); 
        filtselect.setAttribute('data-live-search',"true"); 
        updatemenu(field);
        document.getElementById('selectlist').appendChild(filtselect);
        $('#' +field).selectpicker('refresh');
        if (['morph_attributes','struct_domain'].includes(field)) {
            updatemenu(field);
            $('#' +field).selectpicker('refresh');
        }
    }
        

}

function updatemenus() {
    var tohide = ['max_age','min_age','min_weight','max_weight'];
    //tohide.forEach(element => {
    //    var anelem = document.getElementById(element).parentElement.style.display = 'None';
    //});
    getfieldvals(fields).then(data => {
        data.forEach(elem => {
            var output = [];

            $.each(elem.vals, function(key,value)
            {
                output.push('<option value="'+ value +'">'+ value +'</option>');
            });

            $('#' + elem.field).html(output.join(''));
            $('#' + elem.field).selectpicker('refresh');

        });
        //  document.getElementsByClassName("spinner-border")[0].style.display = 'none';
        
            
    });
    

}

function selectrefresher() {
    $('.selectpicker').selectpicker('refresh');
}


function metasearch(countonly=false) {
    theform = document.getElementById('searchform');
    var formdata = new FormData(theform);
    params = new URLSearchParams();
    
    for (var pair of formdata.entries()) {
        params.append(pair[0],pair[1]);
      }
    if (Array.from(params).length == 0) {
        alert('Please provide search parameters before searching.');
        return;
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