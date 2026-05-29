# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from django.db.models.manager import BaseManager

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core.units import WEIGHT_UNIT_CHOICES, WEIGHT_UNIT_KG, convert_weight, get_default_unit


def weight_change(
    actual_weights: BaseManager, percentile_weights: BaseManager, birthday: datetime
):
    """
    Create a graph showing weight over time.
    :param actual_weights: a QuerySet of Weight instances.
    :param percentile_weights: a QuerySet of Weight Percentile instances.
    :param birthday: a datetime of the child's birthday
    :returns: a tuple of the graph's html and javascript.
    """
    actual_weights = actual_weights.order_by("-date")
    default_unit = get_default_unit("weight")

    weighing_dates: list[datetime] = list(actual_weights.values_list("date", flat=True))
    measured_weights = [
        convert_weight(w.weight, w.weight_unit, default_unit)
        if w.weight_unit and w.weight_unit != default_unit
        else w.weight
        for w in actual_weights
    ]

    actual_weights_trace = go.Scatter(
        name=_("Weight"),
        x=weighing_dates,
        y=measured_weights,
        fill="tozeroy",
        mode="lines+markers",
    )

    if percentile_weights:
        dates = list(
            map(
                lambda timedelta: birthday + timedelta,
                percentile_weights.values_list("age_in_days", flat=True),
            )
        )

        # reduce percentile data xrange to end 1 day after last weigh in for formatting purposes
        # https://github.com/babybuddy/babybuddy/pull/708#discussion_r1332335789
        last_date_for_percentiles = min(max(dates), max(weighing_dates))
        dates = dates[: dates.index(last_date_for_percentiles) + 1]

        def pct_vals(field):
            vals = list(percentile_weights.values_list(field, flat=True))
            if default_unit != WEIGHT_UNIT_KG:
                vals = [convert_weight(v, WEIGHT_UNIT_KG, default_unit) for v in vals]
            return vals

        percentile_weight_3_trace = go.Scatter(
            name=_("P3"),
            x=dates,
            y=pct_vals("p3_weight"),
            line={"color": "red"},
        )
        percentile_weight_15_trace = go.Scatter(
            name=_("P15"),
            x=dates,
            y=pct_vals("p15_weight"),
            line={"color": "orange"},
        )
        percentile_weight_50_trace = go.Scatter(
            name=_("P50"),
            x=dates,
            y=pct_vals("p50_weight"),
            line={"color": "green"},
        )
        percentile_weight_85_trace = go.Scatter(
            name=_("P85"),
            x=dates,
            y=pct_vals("p85_weight"),
            line={"color": "orange"},
        )
        percentile_weight_97_trace = go.Scatter(
            name=_("P97"),
            x=dates,
            y=pct_vals("p97_weight"),
            line={"color": "red"},
        )

    data = [
        actual_weights_trace,
    ]
    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Weight") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    unit_label = dict(WEIGHT_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Weight") + (
        f" ({unit_label})" if unit_label else ""
    )
    if percentile_weights:
        # zoom in on the relevant dates
        layout_args["xaxis"]["range"] = [
            birthday,
            max(weighing_dates) + timedelta(days=1),
        ]
        layout_args["yaxis"]["range"] = [0, max(measured_weights) * 1.5]
        data.extend(
            [
                percentile_weight_97_trace,
                percentile_weight_85_trace,
                percentile_weight_50_trace,
                percentile_weight_15_trace,
                percentile_weight_3_trace,
            ]
        )

    fig = go.Figure({"data": data, "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
