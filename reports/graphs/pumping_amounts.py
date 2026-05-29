# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core.units import VOLUME_UNIT_CHOICES, convert_volume, get_default_unit


def pumping_amounts(objects):
    """
    Create a graph showing pumping amounts over time.
    :param instances: a QuerySet of Pumping instances.
    :returns: a tuple of the graph's html and javascript.
    """
    objects = objects.order_by("start")
    default_unit = get_default_unit("volume")

    # We need to find date totals for annotations at the end
    curr_date = ""
    date_totals = {}
    for object in objects:
        date_s = timezone.localtime(object.start)
        date_s = str(date_s.date())
        if curr_date != date_s:
            date_totals[date_s] = 0.0
            curr_date = date_s
        amount = object.amount
        if amount and object.amount_unit and object.amount_unit != default_unit:
            amount = convert_volume(amount, object.amount_unit, default_unit)
        date_totals[date_s] += amount

    dates = []  # Single array for each bar
    amounts = []  # Array of arrays containing amounts
    index_x, index_y = 0, -1
    for object in objects:
        date_s = timezone.localtime(object.start)
        date_s = str(date_s.date())
        if date_s not in dates:
            dates.append(date_s)
            index_y += 1
            index_x = 0
        if len(amounts) == 0 or len(amounts) <= index_x:
            amounts.append([0] * len(date_totals.keys()))
        amount = object.amount
        if amount and object.amount_unit and object.amount_unit != default_unit:
            amount = convert_volume(amount, object.amount_unit, default_unit)
        amounts[index_x][index_y] = amount
        index_x += 1

    traces = []
    for i in range(0, len(amounts)):
        traces.append(
            go.Bar(
                name="Amount",
                x=dates,
                y=amounts[i],
                text=amounts[i],
                hovertemplate=amounts[i],
                showlegend=False,
            )
        )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Total Pumping Amount") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    unit_label = dict(VOLUME_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Pumping Amount") + (
        f" ({unit_label})" if unit_label else ""
    )

    total_labels = [
        {"x": x, "y": total * 1.1, "text": str(total), "showarrow": False}
        for x, total in zip(list(dates), date_totals.values())
    ]

    fig = go.Figure({"data": traces, "layout": go.Layout(**layout_args)})
    fig.update_layout(barmode="stack", annotations=total_labels)
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
