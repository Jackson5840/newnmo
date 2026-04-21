var mouse_x = 0;
var mouse_y = 0;
$(document).mousemove(function(event) {
  mouse_x = event.pageX;
  mouse_y = event.pageY;
});
$('#custom_image_content').hide();

function maketable(specval) {
  $.getJSON(apiurlbase + "/browse/species_name/" + specval, function(datalist) {    
    if (datalist.size > 5000) {
      $(".hideshow").hide();
    } 
    if (document.getElementById('jstree_demo_div').classList.contains('jstree')) {$('#jstree_demo_div').jstree('destroy'); }      
    $('#jstree_demo_div').jstree({ 
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
        $('#custom_image_content').find('img').attr('src', url);
        $('#custom_image_content')
          .css('position', 'absolute')
          .css('top', $node.position().top) // Add about 20 to ensure the div is not hovered when we re-position it.
          .css('left', $node.position().left + $node.width() + 20)
          //.css('top', mouse_y)
          //.css('left', mouse_x + 100)
          .show();
    }
    })
    .on('dehover_node.jstree', function() {
      $('#custom_image_content').hide(); // Need to hide tooltip after we change hover targets.
    });  
  });  
}

function getselleafs() {
  
}

function gettoggled() {
  selected = $('#jstree_demo_div').jstree('get_selected',true)
  params = new URLSearchParams()
  selected.forEach(element => {
    if (element.children.length==0) {
      params.append('names',element.text);
    }
  });
  if (document.getElementById('aux').checked) {
      params.append('aux',1)
  }
  if ([...params].length>0) {
    anchor = document.createElement('a');
    
    anchor.setAttribute('href',apiurlbase + "/getzipped/?" + params);
    anchor.click();
  }
}


$(function () {

  var specval = ""
  loadList();

  

  $("#selectspecies").change(function () {
    specval = document.getElementById("selectspecies").value;
    maketable(specval);
  })

    
  
  function loadList(){
    $.getJSON(apiurlbase + "/metavals/?fields=species_name", function(labsList) {             
      var output = [];  
      $.each(labsList[0].vals, function(key,value)
        {
            output.push('<option value="'+ value +'">'+ value +'</option>');
        });

        $('#selectspecies').html(output.join(''));
        $('#selectspecies').selectpicker('refresh');
    
    });
  }
});