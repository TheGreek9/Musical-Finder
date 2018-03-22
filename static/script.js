$(document).ready(function() {
  // Add scrollspy to <body>
  $('body').scrollspy({
    target: ".navbar",
    offset: 50
  });

  // Add smooth scrolling on all links inside the navbar
  $("#myNavbar").find("a").on('click', function(event) {
    // Make sure this.hash has a value before overriding default behavior
    if ($(this).prop("hash") !== "") {
      // Prevent default anchor click behavior
      event.preventDefault();

      var hash = $(this).prop("hash")
      // Using jQuery's animate() method to add smooth page scroll
      // The optional number (800) specifies the number of milliseconds it takes to scroll to the specified area
      $('html, body').animate({
        scrollTop: $(hash).offset().top
      }, 1000, function() {

        // Add hash (#) to URL when done scrolling (default click behavior)
        window.location.hash = hash;
      });
    } // End if
  });


  $.fn.validator.Constructor.FOCUS_OFFSET = '100';
  var newsongMusical = ""

  $("#search, #newMusical").typeahead({
    minLength: 1,
    hint: false
  }, {
    source: search,
    limit: 10,
    display: function(suggestion) {
      return suggestion.musical
    },
  });

  $("#search").on("typeahead:selected", function(eventObject, suggestion, name) {
    $("#sel").empty();
    if ($(this).val() == "All Musicals") {
      $("#sel").append("<option>All Roles</option>")
      $("#sel").css("pointer-events", "none");
    } else {
      AddRoles(suggestion);
    }
  });

  $("#search").blur(function() {
    if (!$(this).val()) {
      $("#sel").empty();
    } else {}
  });

  newsongMusical = localStorage.getItem("musical");

  if (newsongMusical != "") {
    $("#newMusical").val(newsongMusical);
  }

  if ($("#newMusical").val()) {
    localStorage.setItem("musical", "");
  }

  $("input[name=musicalNon]").click(function() {
    var val = $('input[name=musicalNon]:checked').val();
    if (val == "Musical") {
      $("#artist").prop('required', false);
    } else {
      $("#artist").prop('required', true);
    }
  });

  var validated = false;
  var formName = "#"

});

function submitValidate() {
  var validated = false;
  var formName = "#"

  formName.append($(this).parents('form').attr('id'))

  if (validated == false) {
    $(formName).validator('validate');
  } else {
    $(formName).submit();
    formName = "#";
  }

  $(formName).on("invalid.bs.validator", function() {
    $("#submit").css('opacity', 0.5);
    $("#submit").css('cursor', 'not-allowed');
    validated = false;
  });

  $(formName).on("valid.bs.validator", function() {
    $("#submit").css('opacity', 1);
    $("#submit").css('cursor', 'default');
    validated = true;
  });

}

function search(query, syncResults, asyncResults) {

  var parameters = {
    que: query
  };
  $.getJSON(Flask.url_for("search"), parameters)
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

function AddRoles(suggestion) {
  var options = ""
  var parameters = {
    music: suggestion.musical
  }

  $.getJSON(Flask.url_for("roles"), parameters)
    .done(function(data, textStatus, jqXHR) {
      for (var i = 0; i < data.length; i++) {
        options += "<option>" + data[i].role + "</option>"
      }
      $("#sel").append("<option>All Roles</option>")
      $("#sel").append(options)
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

      // log error to browser's console
      console.log(errorThrown.toString());
    });
}

function passMusical() {
  var musical = $("#resultsMusical").text();
  localStorage.setItem("musical", musical);
}