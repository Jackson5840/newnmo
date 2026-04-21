//import {apiurlbase,getneurons, parseneuronlist} from './base.js'


/**
 * generates a container from a criteria. Lists all neurons and then divides by three
 * @param  {[archive]} archive [which archive to list]
 * @param  {[data]} uploaddate [uploaddate]
 */
//function gencont() {
//var params = {
//    'species_name': 'rat'
//};
var pageparams = new URLSearchParams(window.location.search)
var trees = [];
function toggleall(value) {
    checkboxes = document.getElementsByClassName('dlcheck');
    for (var checkbox of checkboxes) {
        checkbox.checked = value;
    }
}

function selectall() {
    trees.forEach(element => {
        $('#'+element).jstree(true).check_all();
    });
}

function deselectall() {
    trees.forEach(element => {
        $('#'+element).jstree(true).uncheck_all();
    });
}

function gettreesel() {
    params = new URLSearchParams()
    trees.forEach(element => {
        selected = $('#'+element).jstree('get_selected',true)  
        selected.forEach(sel_element => {
            if (sel_element.children.length==0) {
                params.append('names',sel_element.text);
        }
    });
    });
    checkl = 0;
    if (document.getElementById('aux').checked) {
        params.append('aux',1)
        checkl += 1;
    }
    if ([...params].length>checkl && trees.length>0) {
      anchor = document.createElement('a');
      
      anchor.setAttribute('href',apiurlbase + "/getzipped/?" + params);
      anchor.click();
    }
  }

function gettoggled() {
    params = new URLSearchParams()
    checkboxes = document.getElementsByClassName('dlcheck');
    for (var checkbox of checkboxes) {
        if (checkbox.checked) {
            params.append('names',checkbox.id)
        }
    } 
    if (document.getElementById('aux').checked) {
        params.append('aux',1)
    }
    if (trees.length == 0) {
        anchor = document.createElement('a');
        anchor.setAttribute('href',apiurlbase + "/getzipped/?" + params);
        anchor.click();
    }
}

function genlielem(ulelem,htext,newparams,pagetarget=htext) {
    var lielem = document.createElement("li");
    lielem.setAttribute('class','page-item');
    var hyperl = document.createElement("a");
    hyperl.setAttribute('class','page-link');
    var qstring = new URLSearchParams(newparams);
    qstring.delete('page');
    qstring.append('page',pagetarget);
    let path = window.location.href.split('?')[0]
    hyperl.setAttribute('href',path +'?' + qstring);
    hyperl.innerHTML = htext;
    lielem.appendChild(hyperl);
    ulelem.appendChild(lielem);
}

function updateneurons(params) {
    getneurons(params).then((neurons) => {
        var idlistkey = neurons.idlistkey;
        var currentpage;
        if (params.has('page')) {
            currentpage = parseInt(params.get('page'));
        }
        else {
            currentpage = 1;
        }
        
        document.getElementById('nneurons').innerHTML = neurons.total + ' neurons found';
        
        
        var npages = Math.ceil(neurons.total/neurons.size);
        
        if (neurons.total == 0) {
            return;
            
        }

        if (params.has('browse')) {
            
                
            
            // 1) fetch all 
            getfieldvals([params.get('browse')],'',idlistkey).then((fieldvals) => {
                neuronlist = document.getElementById("neuronlist");
                if (neurons.total < 5000) {
                    cbutton = document.createElement("button");
                    cbutton.setAttribute("type","button");
                    cbutton.setAttribute("class","btn btn-primary")
                    cbutton.setAttribute("onclick","$('.jstree').jstree('close_all');")
                    cbutton.innerText= "Close All";
                    neuronlist.appendChild(cbutton);
                    selem = document.createElement("span");
                    selem.innerHTML = '&nbsp;'
                    neuronlist.appendChild(selem);

                    obutton = document.createElement("button");
                    obutton.setAttribute("type","button");
                    obutton.setAttribute("class","btn btn-primary")
                    obutton.setAttribute("onclick","$('.jstree').jstree('open_all');")
                    obutton.innerText= "Open All";
                    neuronlist.appendChild(obutton);

                }
                else {
                    document.getElementById('nneurons').innerHTML = '> 5000 neurons found, limiting result set 5k';
                }
                fieldvals[0].vals.forEach(element => {
                    treeid = element.replace(/ /g,"_");
                    row = document.createElement("div");
                    trees.push(treeid);
                    row.setAttribute("class","row");
                    row.setAttribute("id",treeid);
                    neuronlist.appendChild(row);
                    maketree(element,fieldvals[0].field,treeid,"floating_image",idlistkey);
                });
            });
        }
        else {
            parseneuronlist(neurons.data,'neuronlist');


            var index = currentpage;
            var maxindex = currentpage + 10;
            var pglist = document.getElementById('pglist');
            pglist.innerHTML='';
            if (currentpage>1) {
                genlielem(pglist,'&lt;',params,Math.max(currentpage-10,1));   
            }
            while (index <= npages && index < maxindex) {
                genlielem(pglist,index,params);
                index++;
            }
            if (index<npages) {
                genlielem(pglist,`...${npages}`,params,npages);
                
            }
            if (maxindex<npages) {
                genlielem(pglist,'&gt;',params,maxindex);    
            }
        }            
    
    })
}



//

//}