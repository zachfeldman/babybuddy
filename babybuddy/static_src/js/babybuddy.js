if (typeof jQuery === "undefined") {
  throw new Error("Baby Buddy requires jQuery.");
}

/**
 * Baby Buddy Namespace
 *
 * Default namespace for the Baby Buddy app.
 *
 * @type {{}}
 */
var BabyBuddy = (function () {
  return {};
})();

/**
 * Pull to refresh.
 *
 * @type {{init: BabyBuddy.PullToRefresh.init, onRefresh: BabyBuddy.PullToRefresh.onRefresh}}
 */
BabyBuddy.PullToRefresh = (function (ptr) {
  return {
    init: function () {
      ptr.init({
        mainElement: "body",
        onRefresh: this.onRefresh,
      });
    },

    onRefresh: function () {
      window.location.reload();
    },
  };
})(PullToRefresh);

/**
 * Show a loading spinner on the submit button when a form is submitted and
 * prevent double-submission.
 */
(function handleFormSubmit() {
  $("form").on("submit", function (event) {
    var submitter =
      (event.originalEvent && event.originalEvent.submitter) ||
      $(this).find('[type="submit"]')[0];
    if (!submitter || $(submitter).prop("disabled")) return;
    $(submitter)
      .prop("disabled", true)
      .prepend(
        '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>',
      );
  });
})();

BabyBuddy.RememberAdvancedToggle = function (ptr) {
  localStorage.setItem("advancedForm", event.newState);
};

(function toggleAdvancedFields() {
  window.addEventListener("load", function () {
    if (localStorage.getItem("advancedForm") !== "open") {
      return;
    }

    document.querySelectorAll(".advanced-fields").forEach(function (node) {
      node.open = true;
    });
  });
})();

(function handleQuickEntry() {
  function getCsrfToken() {
    var el = document.querySelector("[name=csrfmiddlewaretoken]");
    return el ? el.value : "";
  }

  function getParseUrl() {
    var modal = document.getElementById("quick-entry-modal");
    return modal ? modal.getAttribute("data-parse-url") : null;
  }

  function getChildSlug() {
    var el = document.getElementById("quick-entry-child");
    return el ? el.value : "";
  }

  function parse() {
    var text = $("#quick-entry-text").val().trim();
    if (!text) return;
    var parseUrl = getParseUrl();
    if (!parseUrl) return;

    $("#quick-entry-preview").addClass("d-none");
    $("#quick-entry-error").addClass("d-none");
    var $btn = $("#quick-entry-parse-btn");
    $btn.prop("disabled", true).text("Parsing…");

    $.ajax({
      url: parseUrl,
      method: "POST",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: { text: text, child: getChildSlug() },
      success: function (data) {
        if (data.error) {
          $("#quick-entry-error").text(data.error).removeClass("d-none");
        } else {
          $("#quick-entry-preview-text").text(data.preview);
          $("#quick-entry-open-form").attr("href", data.redirect_url);
          $("#quick-entry-preview").removeClass("d-none");
        }
      },
      error: function () {
        $("#quick-entry-error")
          .text("An error occurred. Please try again.")
          .removeClass("d-none");
      },
      complete: function () {
        $btn.prop("disabled", false).text("Parse");
      },
    });
  }

  $(document).on("click", "#quick-entry-parse-btn", parse);

  $(document).on("keydown", "#quick-entry-text", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      parse();
    }
  });

  $(document).on("show.bs.modal", "#quick-entry-modal", function () {
    $("#quick-entry-text").val("");
    $("#quick-entry-preview").addClass("d-none");
    $("#quick-entry-error").addClass("d-none");
  });

  $(document).on("shown.bs.modal", "#quick-entry-modal", function () {
    $("#quick-entry-text").trigger("focus");
  });
})();
