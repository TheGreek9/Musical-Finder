$(document).ready(function() {
  $.fn.validator.Constructor.FOCUS_OFFSET = '100';
  var newsongMusical = ""

    $("#search").typeahead({
        minLength: 1,
        hint: false
    },
    {
        source: search,
        limit: 10,
        display: function(suggestion) { return suggestion.musical},
    });

    $("#newMusical").typeahead({
        minLength: 1,
        hint: false
    },
    {
        source: search,
        limit: 10,
        display: function(suggestion) { return suggestion.musical},
    });

    $("#search").on("typeahead:selected", function(eventObject, suggestion, name) {
        $("#sel").empty();
        if($(this).val() == "All Musicals") {
          $("#sel").append("<option>All Roles</option>")
          $("#sel").css("pointer-events", "none");
        }
        else {
          AddRoles(suggestion);
        }
    });

    $("#search").blur(function(){
      if( !$(this).val() ) {
        $("#sel").empty();
      }
      else {
      }
    });

    newsongMusical = localStorage.getItem("musical");

    if(newsongMusical != "") {
      $("#newMusical").val(newsongMusical);
    }

    if($("#newMusical").val()){
      localStorage.setItem("musical", "");
    }

    var validated = false;

    $("#submit").click(function(){
      if (validated == false) {
        $("#newsongform").validator('validate');
      }
      else{
        $("#newsongform").submit();
      }
    });

    $("#newsongform").on("invalid.bs.validator", function(){
      $("#submit").css('opacity',0.5);
      $("#submit").css('cursor','not-allowed');
      validated = false;
    });

    $("#newsongform").on("valid.bs.validator", function(){
      $("#submit").css('opacity',1);
      $("#submit").css('cursor','default');
      validated = true;
    });



});

function search(query, syncResults, asyncResults)
{

    var parameters = {
        que: query
    };
    $.getJSON(Flask.url_for("search"),parameters)
    .done(function(data, textStatus, jqXHR) {
        // call typeahead's callback with search results (i.e., places)
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());

        // call typeahead's callback with no results
        asyncResults([]);
    });

}

function AddRoles(suggestion)
{
  var options = ""
  var parameters = {
      music: suggestion.musical
  }

  $.getJSON(Flask.url_for("roles"), parameters)
  .done(function(data, textStatus, jqXHR) {
      for (var i = 0; i < data.length; i++)
          {
              options += "<option>" + data[i].role + "</option>"
          }
          $("#sel").append(options)
          $("#sel").append("<option>All Roles</option>")
  })
  .fail(function(jqXHR, textStatus, errorThrown) {

      // log error to browser's console
      console.log(errorThrown.toString());
  });
}

function passMusical()
{
    var musical = $("#resultsMusical").text();
    localStorage.setItem("musical", musical);
}
