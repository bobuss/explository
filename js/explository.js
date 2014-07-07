
window.onload = function() {

  var form = document.getElementById("form");
  form.addEventListener('submit',function(e) {
    e.preventDefault();

    var inputPath = document.getElementById("input-path").value;

    dsv("/commits/"+inputPath, render).response(function(request) {

      document.getElementById("fun-stats").className = "";

      return dsv.parseRows(request.responseText, function(d) {
        // datetime|author
        // "2013-10-17T18:14:56Z|Bertrand TORNIL"
        var datetime = datetimeFormat.parse(d[0]);
        return {
          datetime: datetime,
          date : new Date(datetime.getFullYear(),
                          datetime.getMonth(),
                          datetime.getDate()),
          author: d[1].toLowerCase()
        };
      });

    });

    return false;

  }, false);
};


//
// GIT statistics
//

var authorsChart = dc.rowChart(".authors-chart");
var hourOfDayChart = dc.barChart(".hour-of-day-chart");
var dayOfWeekChart = dc.rowChart(".day-of-week-chart");
var volumeChart = dc.barChart(".daily-volume-chart");

var dateFormat = d3.time.format("%Y-%m-%d");
// var datetimeFormat = d3.time.format("%Y-%m-%d %H:%M:%S %Z");
// "2014-04-01T01:33:28Z"
var datetimeFormat = d3.time.format("%Y-%m-%dT%H:%M:%SZ");

var dsv = d3.dsv("|", "text/plain");

var render = function(data) {

  //
  // I. Data part
  //
  var ndx = crossfilter(data);

  var all = ndx.groupAll();

  // authors
  var author = ndx.dimension(function(d) {
    return d.author;
  })
  var authorGroup = author.group();

  // hours of the day
  var hourOfDay = ndx.dimension(function (d) {
    var hour = d.datetime.getHours();
    return hour;
  });
  var hourOfDayGroup = hourOfDay.group();

  // days of the week
  var dayOfWeek = ndx.dimension(function (d) {
    var day = d.datetime.getDay();
    var name=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    return day + "." + name[day];
  });
  var dayOfWeekGroup = dayOfWeek.group();

  // commits by day
  var commitByDays = ndx.dimension(function (d) {
    return d.date;
  });
  var commitByDaysGroup = commitByDays.group();

  //
  // II. Chart parts
  //


  // authors
  authorsChart.width(990)
              .height(30 * authorGroup.size())
              .margins({top: 10, left: 10, right: 10, bottom: 30})
              .dimension(author)
              .group(authorGroup)
              // .ordering(function(d) {
              //    return d.value;
              // })
              .colors(d3.scale.category20())
              .label(function (d) {
                  return d.key;
              })
              .elasticX(true)
              .xAxis().ticks(4);

  // hours of the day
  hourOfDayChart.width(620)
                .height(180)
                .margins({top: 10, right: 10, bottom: 30, left: 40})
                .dimension(hourOfDay)
                .group(hourOfDayGroup)
                .elasticY(true)
                .gap(1)
                .round(dc.round.floor)
                .x(d3.scale.linear().domain([0, 24]))
                .renderHorizontalGridLines(true)
                .filterPrinter(function (filters) {
                    var filter = filters[0], s = "";
                    s += parseInt(filter[0], 10) + "h -> " + parseInt(filter[1], 10) + "h";
                    return s;
                })
                .xAxis()
                .tickFormat(function (v) {
                    return v + "h";
                });

  hourOfDayChart.yAxis().ticks(5);

  // day of the week
  dayOfWeekChart.width(360)
                .height(30 * dayOfWeekGroup.size())
                .margins({top: 10, left: 10, right: 10, bottom: 30})
                .group(dayOfWeekGroup)
                .dimension(dayOfWeek)
                .colors(d3.scale.category10())
                .label(function (d) {
                    return d.key.split(".")[1];
                })
                .title(function (d) {
                    return d.value;
                })
                .elasticX(true)
                .xAxis().ticks(4);

  // commits by day
  volumeChart.width(990)
             .height(160)
             .margins({top: 10, right: 10, bottom: 30, left: 40})
             .dimension(commitByDays)
             .group(commitByDaysGroup)
             .elasticY(true)
             .centerBar(true)
             .gap(0)
             .x(d3.time.scale().domain([commitByDays.bottom(1)[0].date, commitByDays.top(1)[0].date]))
             .round(d3.time.day.round)
             .xUnits(d3.time.days);

  // count selected commits
  dc.dataCount(".dc-data-count").dimension(ndx)
                                .group(all);

  // render everything
  dc.renderAll();
}
