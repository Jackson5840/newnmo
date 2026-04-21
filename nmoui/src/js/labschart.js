$(function () {
	$.getJSON(apiurlbase + "/chartcount/archive_name/800", function(valcounts) { 
				
		Highcharts.chart('bylabcontainer', {
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
					}
				}
			},
			series: [{
				name: 'By Archive',
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