(function($) {
        var PieConfig;
        window.lastupdate = Date.now();

        pageSetUp();

        /* flot chart colors default */
        var $chrt_border_color = "#efefef";
        var $chrt_grid_color = "#DDD"
        var $chrt_main = "#7e9d3a";         /* greeen    */
        var $chrt_second = "#6595b4";       /* blue      */
        var $chrt_third = "#FF9F01";        /* orange    */
        var $chrt_fourth = "#E24913";       /* red       */
        var $chrt_fifth = "#BD362F";        /* dark red  */
        var $chrt_mono = "#000";

        var d = [], e = [], f = [], g = [], h = [];

        var pvchart = function() {
            var options = {
                xaxis : { mode : "time", tickLength : 5, timezone: "browser" },
                series : {
                    lines : {
                        show : true,
                        lineWidth : 1,
                        fill : true,
                        fillColor : {
                            colors : [{
                                opacity : 0.1
                            }, {
                                opacity : 0.15
                            }]
                        }
                    },
                    points: { show: false },
                    shadowSize : 0
                },
                colors : [$chrt_main, $chrt_second, $chrt_third, $chrt_fourth],
            };
            plot_1 = $.plot($("#pvchart"), [d,e,f,g,h], options);
        };

        let socket = new WebSocket("ws://10.0.1.4:6789/")

        socket.onopen = function(e) {
            console.log("[open] Connection established, send -> server");
            socket.send("This is the dashboard client.");
        };

        socket.onmessage = function(event) {
            var timestamp = Date.now(),
                data = JSON.parse(event.data),
                inv = null,
                batt = null;

            $(data).each(function (i, obj) {
                if (obj['DeviceClass'] == 'Solar Inverter') {
                    inv = obj;
                } else {
                    batt = obj;
                }
            });

            var panelpower = inv['AC Power'] || 0;
            var batterypower = batt['AC Power'] || 0;
            var power_from_grid = inv['Power from grid'] || 0;
            var power_to_grid = inv['Power to grid'] || 0;

            var consumption = panelpower + batterypower + power_from_grid - power_to_grid;
            var batterypower = 0 - batterypower;

            d.push([timestamp, panelpower]); /* Solar Dach */
            e.push([timestamp, power_to_grid]); /* Einspeisung */
            f.push([timestamp, batterypower]); /* Batterie */
            g.push([timestamp, consumption]); /* Verbrauch */
            h.push([timestamp, power_from_grid]); /* Netzbezug */
            pvchart();

            $('#panelacpower').text(panelpower);
            $('#powertogrid').text(power_to_grid);
            $('#batteryacpower').text(batterypower);
            $('#batterycapacity').text(batt['BatteryCharge']);
            $('#powerfromgrid').text(power_from_grid);
            $('#consumption').text(consumption);

            $('#batterycharging').find('i').removeClass('fa-caret-up');
            $('#batterycharging').find('i').removeClass('fa-caret-down');
            $('#batterycharging').removeClass('bg-color-green');
            $('#batterycharging').removeClass('bg-color-red');
            if (batt['BatteryState'] === 'Charging') {
                $('#batterycharging').find('i').addClass('fa-caret-up');
                $('#batterycharging').addClass('bg-color-green');
            } else {
                $('#batterycharging').find('i').addClass('fa-caret-down');
                $('#batterycharging').addClass('bg-color-red');
            }
            $('#batterytemp').text(batt['BatteryTemp']);
            $('#panelstatus').removeClass('glyphicon-ok-cirle');
            $('#panelstatus').removeClass('glyphicon-remove-cirle');
            if (inv['Status'] === 'OK') {
                $('#panelstatus').addClass('glyphicon-ok-circle');
            } else {
                $('#panelstatus').addClass('glyphicon-remove-circle');
            }

            window.lastupdate = Date.now();
            console.log(data);
        };

        /* last updated counter */
        setInterval(function() {
            var now = new Date().getTime();
            var distance = now - window.lastupdate;
            var days = Math.floor(distance / (1000 * 60 * 60 * 24));
            var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((distance % (1000 * 60)) / 1000);
            var result = '';
            if (days) { result += days + ' Tagen '; }
            if (hours) { result += hours + ' Stunden '; }
            if (minutes) { result += minutes + ' Minuten '; }
            result += seconds + ' Sekunden ';
            $('#secondslastupdate').text(result);
        }, 1000);
}(jQuery));
