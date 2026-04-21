$(function () {
	$.getJSON(apiurlbase + "/chartcount/region_name/2000", function(valcounts) { 
			
		Highcharts.chart('regioncontainer', {
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
			startAngle: 78
				}
			},
			series: [{
				name: 'By Brain Region',
				point: {
					events: {
					click: function() {
						maketable(this.name);
					}
					}
				},
				colorByPoint: true,
				data: valcounts
			}]
		});
	
	});


}); 