# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core import models
from core.units import VOLUME_UNIT_CHOICES, convert_volume, get_default_unit


def feeding_amounts(instances):
    """
    Create a graph showing daily feeding amounts over time.
    :param instances: a QuerySet of Feeding instances.
    :returns: a tuple of the graph's html and javascript.
    """
    default_unit = get_default_unit("volume")

    feeding_types, feeding_types_desc = map(
        list, zip(*models.Feeding._meta.get_field("type").choices)
    )
    total_idx = len(feeding_types) + 1  # +1 for aggregate total
    totals_list = list()
    for i in range(total_idx):
        totals_list.append({})
    for instance in instances:
        end = timezone.localtime(instance.end)
        date = end.date()
        if date not in totals_list[total_idx - 1].keys():
            for item in totals_list:
                item[date] = 0
        amount = instance.amount or 0
        if amount and instance.amount_unit and instance.amount_unit != default_unit:
            amount = convert_volume(amount, instance.amount_unit, default_unit)
        feeding_idx = feeding_types.index(instance.type)
        totals_list[feeding_idx][date] += amount
        totals_list[total_idx - 1][date] += amount
    zeros = [0 for a in totals_list[total_idx - 1].values()]

    # sum each feeding type for graph
    amounts_array = []
    for i in range(total_idx):
        amounts_array.append([round(a, 2) for a in totals_list[i].values()])

    traces = []
    for i in range(total_idx - 1):
        for x in amounts_array[i]:
            if x != 0:  # Only include if it has non zero values
                traces.append(
                    go.Bar(
                        name=str(feeding_types_desc[i]),
                        x=list(totals_list[total_idx - 1].keys()),
                        y=amounts_array[i],
                        text=amounts_array[i],
                        hovertemplate=str(feeding_types_desc[i]),
                    )
                )
                break

    traces.append(
        go.Bar(
            name=_("Total"),
            x=list(totals_list[total_idx - 1].keys()),
            y=zeros,
            hoverinfo="text",
            textposition="outside",
            text=amounts_array[total_idx - 1],
            showlegend=False,
        )
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Total Feeding Amount by Type") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    unit_label = dict(VOLUME_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Feeding amount") + (
        f" ({unit_label})" if unit_label else ""
    )

    fig = go.Figure({"data": traces, "layout": go.Layout(**layout_args)})
    fig.update_layout(barmode="stack")
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
