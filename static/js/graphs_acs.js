$(function () {
    $.getJSON('http://mayordomo.bramez.com:8080/data/caldera', function (data) {

        for (var i = 0; i < data.length; i++) {
            {
                data[i][0] = Date.parse(data[i][0]);
            }
        }

        Highcharts.setOptions({
            global: {
                timezoneOffset: -60
            }
        });
        $('#container').highcharts({

            chart: {
                zoomType: 'x',
                resetZoomButton: {
                    position: {
                        // align: 'right', // by default
                        // verticalAlign: 'top', // by default
                        x: 0,
                        y: -90
                    }
                }
            },
            title: {
                text: 'Temperaturas ACS'
            },
            subtitle: {
                text: document.ontouchstart === undefined ?
                    'Haz click y arrastra la zona que quieras' : 'Pinch the chart to zoom in'
            },
            xAxis: {
                type: 'datetime'

            },
            yAxis: {
                title: {
                    text: 'Temperaturas'
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    fillColor: {
                        linearGradient: {
                            x1: 0,
                            y1: 0,
                            x2: 0,
                            y2: 1
                        },
                        stops: [
                            [0, Highcharts.getOptions().colors[0]],
                            [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                        ]
                    },
                    spline: {
                        marker: {
                            enabled: true
                        }
                    },
                    marker: {
                        radius: 2
                    },
                    lineWidth: 1,
                    states: {
                        hover: {
                            lineWidth: 1
                        }
                    },
                    threshold: null
                }
            },

            series: [{
                type: 'area',
                name: 'Temperaturas',
                data: data
            }]
        });
    });
});