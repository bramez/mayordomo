var mayordomoApp = angular.module("mayordomo-app", []);

mayordomoApp.controller("MayordomoController", function ($http, $scope) {
    getDevices();

    function getDevices() {


        $http.get("http://mayordomo.bramez.com:8080/devices").success(function (data, status, headers, config) {
            temperaturaACS = data['acs'].temperature;
            temperaturaCalefaccionJordi = data['jordi'].temperature;
            temperaturaCalefaccionNuri = data['nuri'].temperature
            temperaturaCalefaccionPapa = data['papa'].temperature

            $scope.devices = data;

            if (temperaturaACS != null)
                chartCaldera.series[0].points[0].update(temperaturaACS);

            if (temperaturaCalefaccionJordi != null)
                chartCalefaccionJordi.series[0].points[0].update(temperaturaCalefaccionJordi);

            if (temperaturaCalefaccionPapa != null)
                chartCalefaccionPapa.series[0].points[0].update(temperaturaCalefaccionPapa);

            if (temperaturaCalefaccionNuri != null)
                chartCalefaccionNuri.series[0].points[0].update(temperaturaCalefaccionNuri);
        });
    }


    setInterval(getDevices, 10000);


    function setColorCaldera(color) {
        chartCaldera.yAxis[0].plotLinesAndBands[3].svgElem.attr({
            fill: color
        });
    }


    $scope.toggleDevice = function (name, device, chartCaldera, $scope) {
        console.log(device['soft_status'])
        device['soft_status'] = !device['soft_status'];

        $http.put("http://mayordomo.bramez.com:8080/devices/" + name + "/rele", device).success(function (result) {
            console.log(result);
            getDevices()
        }).error(function () {
            device['soft_status'] = !device['soft_status'];
            console.log("error");
        });
    }


    var chartCaldera = new Highcharts.Chart(calderaChartOptions);
    var chartCalefaccionJordi = new Highcharts.Chart(calefaccionJordiOptions);
    var chartCalefaccionPapa = new Highcharts.Chart(calefaccionPapaOptions);
    var chartCalefaccionNuri = new Highcharts.Chart(calefaccionNuriOptions);
})
;