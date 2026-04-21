$(function () {
	$.getJSON(apiurlbase + "/chartcount/species_name/800", function(valcounts) { 
			
		Highcharts.chart('speciescontainer', {
			chart: {
				plotBackgroundColor: null,
				plotBorderWidth: null,
				plotShadow: false,
				borderWidth: 1,
				borderRadius: 10,
				borderColor: "#ccc",
				type: 'pie'
			},
			title: {
				text: ''
			},
			tooltip: {
				pointFormat: '{point.y}'
			},
	/* 			    exporting: {
				allowHTML: true
			}, */
			plotOptions: {
				pie: {
					allowPointSelect: true,
					cursor: 'pointer',
					size : 340,
					dataLabels: {
						enabled: true,
						format: '{point.name} ({point.y}) ',
						distance : 20,
						style: {
							"color": "contrast", "fontSize": "11px", "fontWeight": "regular", "textOutline": "1px contrast" 
						}
					},
			startAngle: 90
				}
			},
			series: [{
				name: 'By Species',
				point: {
					events: {
					click: function() {
						maketable(this.name);
						/* location.href = "#top"; */
	/* 							   e.preventDefault(); */
					}
					}
				},
				colorByPoint: true,
				data: valcounts
			}]
		});
	});

});

