# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from django.db.models.manager import BaseManager

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core.units import HEIGHT_UNIT_CHOICES, HEIGHT_UNIT_CM, convert_height, get_default_unit


def height_change(
    actual_heights: BaseManager, percentile_heights: BaseManager, birthday: datetime
):
    """
    Create a graph showing height over time.
    :param actual_heights: a QuerySet of Height instances.
    :param percentile_heights: a QuerySet of Height Percentile instances.
    :param birthday: a datetime of the child's birthday
    :returns: a tuple of the graph's html and javascript.
    """
    actual_heights = actual_heights.order_by("-date")
    default_unit = get_default_unit("height")

    measuring_dates: list[datetime] = list(
        actual_heights.values_list("date", flat=True)
    )
    measured_heights = [
        convert_height(h.height, h.unit, default_unit)
        if h.unit and h.unit != default_unit
        else h.height
        for h in actual_heights
    ]

    actual_heights_trace = go.Scatter(
        name=_("Height"),
        x=measuring_dates,
        y=measured_heights,
        fill="tozeroy",
        mode="lines+markers",
    )

    if percentile_heights:
        dates = list(
            map(
                lambda timedelta: birthday + timedelta,
                percentile_heights.values_list("age_in_days", flat=True),
            )
        )

        # reduce percentile data xrange to end 1 day after last height measurement in for formatting purposes
        # https://github.com/babybuddy/babybuddy/pull/708#discussion_r1332335789
        last_date_for_percentiles = min(max(dates), max(measuring_dates))
        dates = dates[: dates.index(last_date_for_percentiles) + 1]

        def pct_vals(field):
            vals = list(percentile_heights.values_list(field, flat=True))
            if default_unit != HEIGHT_UNIT_CM:
                vals = [convert_height(v, HEIGHT_UNIT_CM, default_unit) for v in vals]
            return vals

        percentile_height_3_trace = go.Scatter(
            name=_("P3"),
            x=dates,
            y=pct_vals("p3_height"),
            line={"color": "red"},
        )
        percentile_height_15_trace = go.Scatter(
            name=_("P15"),
            x=dates,
            y=pct_vals("p15_height"),
            line={"color": "orange"},
        )
        percentile_height_50_trace = go.Scatter(
            name=_("P50"),
            x=dates,
            y=pct_vals("p50_height"),
            line={"color": "green"},
        )
        percentile_height_85_trace = go.Scatter(
            name=_("P85"),
            x=dates,
            y=pct_vals("p85_height"),
            line={"color": "orange"},
        )
        percentile_height_97_trace = go.Scatter(
            name=_("P97"),
            x=dates,
            y=pct_vals("p97_height"),
            line={"color": "red"},
        )

    data = [
        actual_heights_trace,
    ]
    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Height") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    unit_label = dict(HEIGHT_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Height") + (
        f" ({unit_label})" if unit_label else ""
    )
    if percentile_heights:
        # zoom in on the relevant dates
        layout_args["xaxis"]["range"] = [
            birthday,
            max(measuring_dates) + timedelta(days=1),
        ]
        layout_args["yaxis"]["range"] = [0, max(measured_heights) * 1.5]
        data.extend(
            [
                percentile_height_97_trace,
                percentile_height_85_trace,
                percentile_height_50_trace,
                percentile_height_15_trace,
                percentile_height_3_trace,
            ]
        )

    fig = go.Figure({"data": data, "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
