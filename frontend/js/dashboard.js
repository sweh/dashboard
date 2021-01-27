(function($) {
        var PieConfig;
        var rss_messages = [];
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
                colors : [$chrt_main, $chrt_second, $chrt_third, $chrt_fourth, $chrt_fifth],
            };
            plot_1 = $.plot($("#pvchart"), [d,e,f,g,h], options);
        };

        var handle_rss = function (data) {
            if (!rss_messages.length) {
                container = $('#rsswidget li:first()');
            } else {
                container = $('#rsswidget li:first()').clone();
                $('#rsswidget').prepend(container);
            }
            rss_messages.push(data);
            container.find('.title').text(data.title);
            container.find('.title').attr('href', data.link);
            container.find('.description').text(data.description);
            container.removeClass('hidden');
        };

        var handle_helios = function (data) {
            $(
                ['aussenluft', 'abluft', 'abluft_feuchte', 'fortluft', 'zuluft']
            ).each(function (i, key) {
                $('#helios_' + key).text(data[key]);
                $('#helios_' + key + '_tendency').removeClass('fa-caret-down');
                $('#helios_' + key + '_tendency').removeClass('fa-caret-up');
                $('#helios_' + key + '_tendency').removeClass('fa-caret-right');
                $('#helios_' + key + '_tendency').addClass(
                    'fa-caret-' + data[key + '_tendency']
                );
            });
            $('#helios_stufe').val(data['stufe']);
            $('#helios_stufe').knob({
                release: function (value) {
                    window.socket.send(
                        JSON.stringify({'helios_stufe': value})
                    );
                },
            });
        };

        var handle_corona = function (odata) {
            var data = odata.data[15091],
                meta = odata.meta;
            var incidence = Math.round(data.weekIncidence),
                last_update = new Date(meta.lastUpdate).toLocaleDateString(),
                source = meta.source;

            $('#corona_incidence').removeClass('txt-color-yellow')
            $('#corona_incidence').removeClass('txt-color-redLight')
            $('#corona_incidence').removeClass('txt-color-red')
            $('#corona_incidence').removeClass('txt-color-magenta')
            incidence_class = '';
            if (incidence > 35) {
                incidence_class = 'txt-color-yellow';
            }
            if (incidence > 50) {
                incidence_class = 'txt-color-redLight';
            }
            if (incidence > 100) {
                incidence_class = 'txt-color-red';
            }
            if (incidence > 200) {
                incidence_class = 'txt-color-magenta';
            }
            $('#corona_incidence').addClass(incidence_class)
            $('#corona_incidence').text(incidence);
            $('#corona_date').text(last_update);
            $('#corona_source').text(source);
            $('#corona_cases_delta').text(data.delta.cases);
            $('#corona_deaths_delta').text(data.delta.deaths);
            $('#corona_recovered_delta').text(data.delta.recovered);
        }

        var handle_weather = function (data) {
            var current_temp = data.out_temp,
                today_temp_min = data.out_temp_min,
                today_temp_max = data.out_temp_max,
                current_wind_str = data.wind_str,
                current_wind_angle = data.wind_angle,
                current_wind_icon,
                current_wind_desc,
                current_rain = data.rain || '0.0',
                current_rain_1 = data.rain_1 || '0.0',
                current_rain_24 = data.rain_24 || '0.0',
                weather_icon = data.weather[0].icon,
                weather_desc = data.weather[0].description;

            if (current_wind_angle >= 315 && current_wind_angle < 45 ) {
                current_wind_angle = 'N';
                current_wind_icon = 'fa-chevron-down';
            } else if (current_wind_angle >= 45 && current_wind_angle < 135 ) {
                current_wind_angle = 'O';
                current_wind_icon = 'fa-chevron-left';
            } else if (current_wind_angle >= 135 && current_wind_angle < 225 ) {
                current_wind_angle = 'S';
                current_wind_icon = 'fa-chevron-up';
            } else {
                current_wind_angle = 'W';
                current_wind_icon = 'fa-chevron-right';
            }
            if (current_wind_str == 0) {
                current_wind_desc = 'Stille';
            } else if (current_wind_str > 0 && current_wind_str <= 3) {
                current_wind_desc = 'schwacher Wind';
            } else if (current_wind_str == 4) {
                current_wind_desc  = 'mäßiger Wind';
            } else if (current_wind_str == 5) {
                current_wind_desc = 'frischer Wind';
            } else if (current_wind_str == 6 || current_wind_str == 7) {
                current_wind_desc = 'starker Wind';
            } else if (current_wind_str == 8 || current_wind_str == 9) {
                current_wind_desc = 'Sturm';
            } else if (current_wind_str == 10) {
                current_wind_desc = 'schwerer Sturm';
            } else if (current_wind_str == 11 || current_wind_str == 12) {
                current_wind_desc = 'Orkan';
            }

            $('#current_temp').text(current_temp);
            $('#today_temp_max').text(today_temp_max);
            $('#today_temp_min').text(today_temp_min);
            $('#weather_desc').text(weather_desc);
            $('#weather_wind_icon').removeClass('fa-chevron-down');
            $('#weather_wind_icon').removeClass('fa-chevron-left');
            $('#weather_wind_icon').removeClass('fa-chevron-up');
            $('#weather_wind_icon').removeClass('fa-chevron-right');
            $('#weather_wind_icon').addClass(current_wind_icon);
            $('#weather_wind_angle').text(current_wind_angle + ' ' + current_wind_str);
            $('#weather_wind_desc').text(current_wind_desc);
            $('#weather_rain').text(current_rain + ' l');
            $('#weather_rain_1').text(current_rain_1 + ' l');
            $('#weather_rain_24').text(current_rain_24 + ' l');
            $('#current_weather_icon').attr(
                'src',
                'http://openweathermap.org/img/wn/' + weather_icon + '@2x.png'
            );
        }

        var handle_pv = function (data) {
            timestamp = new Date(data.timestamp);

            var panelpower = data['AC Power Solar'] || 0;
            var batterypower = data['AC Power Battery'] || 0;
            var power_from_grid = data['Power from grid'] || 0;
            var power_to_grid = data['Power to grid'] || 0;

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
            $('#batterycapacity').text(data['BatteryCharge']);
            $('#powerfromgrid').text(power_from_grid);
            $('#consumption').text(consumption);

            $('#batterycharging').find('i').removeClass('fa-caret-up');
            $('#batterycharging').find('i').removeClass('fa-caret-down');
            $('#batterycharging').removeClass('bg-color-green');
            $('#batterycharging').removeClass('bg-color-red');
            if (data['BatteryState'] === 'Charging') {
                $('#batterycharging').find('i').addClass('fa-caret-up');
                $('#batterycharging').addClass('bg-color-green');
            } else {
                $('#batterycharging').find('i').addClass('fa-caret-down');
                $('#batterycharging').addClass('bg-color-red');
            }
            $('#batterytemp').text(data['BatteryTemp']);
            $('#panelstatus').removeClass('glyphicon-ok-cirle');
            $('#panelstatus').removeClass('glyphicon-remove-cirle');
            if (data['Status Solar'] === 'OK') {
                $('#panelstatus').addClass('glyphicon-ok-circle');
            } else {
                $('#panelstatus').addClass('glyphicon-remove-circle');
            }
        };

        window.socket = new WebSocket('ws://' + window.location.hostname + '/wsapp/');

        window.socket.onopen = function(e) {
            console.log("[open] Connection established, send -> server");
        };

        window.socket.onmessage = function(event) {
            var timestamp = Date.now(),
                data = JSON.parse(event.data);

            if (data['DeviceClass'] === 'Weather') {
                handle_weather(data);
            } else if (data['DeviceClass'] === 'Corona') {
                handle_corona(data);
            } else if (data['DeviceClass'] === 'Helios') {
                handle_helios(data);
            } else if (data['DeviceClass'] === 'RSS') {
                handle_rss(data);
            } else if (data['DeviceClass'] === 'PV') {
                handle_pv(data);
            } else {
                alert('ERROR: Unknown DeviceClass ' + data['DeviceClass']);
            }

            window.lastupdate = Date.now();
        };

        window.socket.onclose = function(event) {
            if (event.wasClean) {
                alert(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
            } else {
                // e.g. server process killed or network down
                // event.code is usually 1006 in this case
                alert('[close] Connection died');
            }
        };

        window.socket.onerror = function(error) {
            alert(`[error] ${error.message}`);
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

            var now = new Date();
            var days = [
                'Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag',
                'Freitag', 'Samstag'
            ];
            var months = [
                'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'
            ];

            var day = days[ now.getDay() ];
            var month = months[ now.getMonth() ];
            if (now.getSeconds() % 2 === 0) {
                seperator = ':';
            } else {
                seperator = '&nbsp;';
            }
            $('#current_date').html(
                day + ', der ' +
                now.getDate() + '. ' + month + ' ' + now.getFullYear() +
                ' ' + String(now.getHours()).padStart(2, "0") + seperator +
                String(now.getMinutes()).padStart(2, "0")
            );
        }, 1000);
}(jQuery));
