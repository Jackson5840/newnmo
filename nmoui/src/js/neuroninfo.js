//import {getneurons,getmeasurements,getpvec} from './base.js'


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


function updatevals(params) {
    
    getneurons(params).then((neurons) => {
        
        var domains = {
            'PR': 'Process',
            'NEU': 'Neurites',
            'AX': 'Axon'
        };
        const genders = {
            'M': 'Male',
            'F': 'Female',
            'M/F': 'Male/Female',
            'H': 'Hermafrodite',
            'NR': 'Not reported',
            'Not reported': 'Not reported',
            'Not applicable': 'Not applicable'
        };
        const age_scale = {
            'M': 'months',
            'D': 'days',
            'Y': 'years',
            'Not reported': 'Not reported'
        }
        var element = neurons.data[0];
        var filearchive = element.archive_name.toLowerCase();
        var swcurl = `https://neuromorpho.org/dableFiles/${filearchive}/CNG version/${element.name}.CNG.swc`;
        var swcorgurl = `https://neuromorpho.org/dableFiles/${filearchive}/Source-Version/${element.name}.${element.originalformat_name}`;
        var stdurl = `https://neuromorpho.org/dableFiles/${filearchive}/Remaining issues/${element.name}.CNG.swc.std`;
        var stdorgurl = `https://neuromorpho.org/dableFiles/${filearchive}/Standardization log/${element.name}.std`;
        const zipurl = `${apiurlbase}/getzipped/?aux=1&names=${element.name}`
        
        document.getElementById('file_morphstd').setAttribute('href',swcurl);
        document.getElementById('file_morphorg').setAttribute('href',swcorgurl);
        document.getElementById('file_logstd').setAttribute('href',stdurl);
        document.getElementById('file_logorg').setAttribute('href',stdorgurl);
        document.getElementById('file_zip').setAttribute('href',zipurl)

        var webglbutton = document.getElementById('viewwebgl');
        webglbutton.setAttribute('href',`http://cng-nmo-dev3.orc.gmu.edu:8080/swc/api/view?url=https%3A%2F%2Fneuromorpho.org/dableFiles/${filearchive}/CNG%20version/${element.name}.CNG.swc&portable=true`); 
        webglbutton.setAttribute('onclick',"window.open(this.href, '_blank','left=20,top=20,width=520,height=520,toolbar=1,resizable=0');  return false;")

        var gifurl = `https://neuromorpho.org/rotatingImages/${element.name}.CNG.gif`;
        
        var gifbutton = document.getElementById('animation');
        gifbutton.setAttribute('onclick',`winpop('${gifurl}','${element.name}')`);


        for (const key in element) {
            switch (key) {
                case 'id':        
                    document.getElementById('id').innerHTML = 'NMO_' + element[key];
                    break;    
                case 'max_weight':
                    if (element[key] == null) {
                        document.getElementById('max_weight').innerHTML = 'Not reported';
                    }
                    else {
                        document.getElementById('max_weight').innerHTML = element[key] + ' grams';
                    }           
                    break;
                case 'min_weight':
                    if (element[key] == null) {
                        document.getElementById('min_weight').innerHTML = 'Not reported';
                    }
                    else {
                        document.getElementById('min_weight').innerHTML = element[key] + ' grams';
                    }           
                    break;
                case 'slicingthickness':
                    var slthick = element[key];
                    slthick += (slthick == 'Not reported' ? '' : ' &micro;m');
                    document.getElementById('slicingthickness').innerHTML = slthick;
                    break;
                case 'max_age':
                    if (element[key] == null || element[key] == "Not reported") {
                        document.getElementById('max_age').innerHTML = 'Not reported';
                    }
                    else {
                        document.getElementById('max_age').innerHTML = element[key] + ' ' + age_scale[element['age_scale']];
                    }
                    
                    break;
                case 'min_age':
                    if (element[key] == null || element[key] == "Not reported") {
                        document.getElementById('min_age').innerHTML = 'Not reported';
                    }
                    else {
                        document.getElementById('min_age').innerHTML = element[key] + ' ' + age_scale[element['age_scale']];
                    }
                    
                    break;
                
                case 'gender':
                    document.getElementById('gender').innerHTML = genders[element[key]];
                    break;
                case 'magnification':
                    if (element[key] == null || element[key] == "Not reported") {
                        document.getElementById('min_age').innerHTML = 'Not reported';
                    }
                    else {
                        document.getElementById('magnification').innerHTML = element[key] + '<b>x</b>';
                    }
                    
                case 'originalformat_name':
                    //var reconstruction = element.reconstruction + '.' + element.originalformat_name;
                    document.getElementById('originalformat_name').innerHTML = element.originalformat_name;
                    break;
                case 'png_url':
                    document.getElementById('neuronimg').setAttribute('src',element.png_url);
                    break;
                case 'region_array':
                    var region1 = element.region_array[0];
                    var nreg = element.region_array.length;
                    var region2 = (nreg > 1 ? element.region_array[1] : 'Not reported');
                    var region3 = (nreg > 2 ? element.region_array[2] : 'Not reported');
                    region3 += (nreg >3 ? ', ' + element.region_array[3] : '');
                    region3 += (nreg >4 ? ', ' + element.region_array[4] : '');
                    document.getElementById('region1').innerHTML = region1;
                    document.getElementById('region2').innerHTML = region2;
                    document.getElementById('region3').innerHTML = region3;
                        
                    break;
                case 'celltype_array':
                    var celltype1 = element.celltype_array[0];
                    var ncell = element.celltype_array.length;
                    var celltype2 = (ncell > 1 ? element.celltype_array[1] : 'Not reported');
                    var celltype3 = (ncell > 2 ? element.celltype_array[2] : 'Not reported');
                    celltype3 += (ncell >3 ? ', ' + element.celltype_array[3] : '');
                    celltype3 += (ncell >4 ? ', ' + element.celltype_array[4] : '');
                    document.getElementById('celltype1').innerHTML = celltype1;
                    document.getElementById('celltype2').innerHTML = celltype2;
                    document.getElementById('celltype3').innerHTML = celltype3;

                    break;
                case 'structural_domain':
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
                    document.getElementById('physint').innerHTML = physint;
                    document.getElementById('structdom').innerHTML = structdom;
                    document.getElementById('morph_attributes').innerHTML = element.structural_domain[0].morph_attributes
                    
                    break;
                default:
                    var viselem = document.getElementById(key);
                    if (viselem!=null) {
                        if (element[key]==null) {
                            viselem.innerHTML = 'Not reported';
                        }
                        else {
                            viselem.innerHTML = element[key];
                        }
                        
                    }
                    break;
                
            }
            
        }
        getmeasurements(element.name).then((neuron) => {
            var measurements = neuron.data[0];
            for (const key in measurements) {
                var val = String(measurements[key]);
                if (val != 'null') {
                    if (['length','width','height','depth','eucdistance','pathdistance'].includes(key)) {
                        val += ' &micro;m';
                    }
                    else if (['soma_surface','surface'].includes(key)) {
                        val += ' &micro;m&sup2;';
                    }
                    else if (['volume'].includes(key)) {
                        val += ' &micro;m&sup3;';
                    }
                    else if (['bif_ampl_local','bif_ampl_remote'].includes(key)) {
                        val += '&deg;';
                        
                    }
                    document.getElementById(key).innerHTML = val;
                }
                else {
                    document.getElementById(key).innerHTML = 'N/A';
                }
            }
            
        })
        getpvec(element.name).then((response) => {
            var pdata = response.data[0];
            var coeffdata = pdata.coeffarray.join(', ');
            var a = document.createElement('a'); 
            var link = document.createTextNode(`${pdata.name}.pvec`);
            a.appendChild(link);
            a.title = `${pdata.name}.pvec`;
            a.onclick = function(){	        	
				var pvecData = `${pdata.distance}, ${pdata.sfactor}\n ${coeffdata}`;
				a.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(pvecData));
                a.setAttribute('download', `${pdata.name}.pvec`);
			}
            document.getElementById('pvec').appendChild(a);
        })
        

    })
        
}



//

//}